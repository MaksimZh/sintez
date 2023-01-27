import unittest
from typing import Any, final, Type

from nodes import DataNode, ProcNode, Procedure, \
    InputData, OutputData, InputProc, OutputProc
from tools import status


class Logger:

    __log: list[Any]

    def __init__(self) -> None:
        super().__init__()
        self.reset_log()
    
    @final
    def log(self, *args: Any) -> None:
        if len(args) == 1:
            self.__log.append(args[0])
        else:
            self.__log.append(tuple(args))

    @final
    def reset_log(self) -> None:
        self.__log = []

    @final
    def get_log(self) -> list[Any]:
        return self.__log


class Test_DataNode(unittest.TestCase):

    class FailingInputProc(InputProc):

        __add_output_status: str
        __validate_status: str

        def __init__(self, add_output_status: str, validate_status: str) -> None:
            super().__init__()
            self.__add_output_status = add_output_status
            self.__validate_status = validate_status
   
        @status()
        def add_output(self, output: OutputData, slot: str) -> None:
            self._set_status("add_output", self.__add_output_status)
        
        @status()
        def validate(self) -> None:
            self._set_status("validate", self.__validate_status)


    class LoggingInputProc(Logger, InputProc):

        __outputs: set[OutputData]

        def __init__(self) -> None:
            super().__init__()
            self.__outputs = set()

        @status()
        def add_output(self, output: DataNode, slot: str) -> None:
            self.__outputs.add(output)
            self._set_status("add_output", "OK")
            self.log("add_output", output, slot)
        
        @status()
        def validate(self) -> None:
            for output in self.__outputs:
                output.put(0)
            self._set_status("validate", "OK")
            self.log("validate")

    
    class LoggingOutputProc(Logger, OutputProc):

        def __init__(self) -> None:
            super().__init__()
        
        @status()
        def invalidate(self, input: InputData) -> None:
            self._set_status("invalidate", "OK")
            self.log("invalidate", input)


    class LoggingProc(LoggingInputProc, LoggingOutputProc):
        pass


    def test_init_no_input(self):
        d = DataNode(str)
        self.assertTrue(d.is_status("init", "OK"))
        self.assertIs(d.get_type(), str)
        self.assertFalse(d.is_valid())


    def test_init_with_input(self):
        i = self.LoggingInputProc()
        d = DataNode(int, i, "a")
        self.assertTrue(d.is_status("init", "OK"))
        self.assertEqual(i.get_log(), [("add_output", d, "a")])
        self.assertIs(d.get_type(), int)
        self.assertFalse(d.is_valid())


    def test_init_with_input_fail(self):
        for status in [
                "INVALID_SLOT_NAME",
                "SLOT_OCCUPIED",
                "ALREADY_LINKED",
                "INCOMPATIBLE_TYPE"]:
            i = self.FailingInputProc(status, "OK")
            d = DataNode(float, i, "a")
            self.assertTrue(d.is_status("init", status))
            self.assertIs(d.get_type(), float)
            self.assertFalse(d.is_valid())


    def test_add_output(self):
        i = self.LoggingProc()
        d = DataNode(int, i, "a")
        o1 = self.LoggingOutputProc()
        self.assertTrue(d.is_status("add_output", "NIL"))
        d.add_output(o1)
        self.assertTrue(d.is_status("add_output", "OK"))
        d.add_output(o1)
        self.assertTrue(d.is_status("add_output", "ALREADY_LINKED"))
        d.add_output(i)
        self.assertTrue(d.is_status("add_output", "ALREADY_LINKED"))


    def test_put(self):
        d = DataNode(complex)
        self.assertTrue(d.is_status("put", "NIL"))
        self.assertFalse(d.is_valid())
        d.put(1 + 2j)
        self.assertTrue(d.is_status("put", "OK"))
        self.assertTrue(d.is_valid())
        d.put(1.5)
        self.assertTrue(d.is_status("put", "OK"))
        self.assertTrue(d.is_valid())
        d.put(1)
        self.assertTrue(d.is_status("put", "OK"))
        self.assertTrue(d.is_valid())
        d.put("foo")
        self.assertTrue(d.is_status("put", "INCOMPATIBLE_TYPE"))
        self.assertTrue(d.is_valid())

    
    def test_put_outputs(self):
        d = DataNode(int)
        o1 = self.LoggingOutputProc()
        d.add_output(o1)
        o2 = self.LoggingOutputProc()
        d.add_output(o2)
        self.assertTrue(d.is_status("put", "NIL"))
        self.assertFalse(d.is_valid())
        d.put(1)
        self.assertTrue(d.is_status("put", "OK"))
        self.assertTrue(d.is_valid())
        self.assertEqual(o1.get_log(), [])
        self.assertEqual(o2.get_log(), [])
        d.put(2)
        self.assertTrue(d.is_status("put", "OK"))
        self.assertTrue(d.is_valid())
        self.assertEqual(o1.get_log(), [("invalidate", d)])
        self.assertEqual(o2.get_log(), [("invalidate", d)])


    def test_get(self):
        d = DataNode(int)
        self.assertTrue(d.is_status("get", "NIL"))
        d.get()
        self.assertTrue(d.is_status("get", "INVALID_DATA"))
        d.put(7)
        self.assertEqual(d.get(), 7)
        self.assertTrue(d.is_status("get", "OK"))


    def test_validate_no_input(self):
        d = DataNode(int)
        self.assertTrue(d.is_status("validate", "NIL"))
        self.assertFalse(d.is_valid())
        d.validate()
        self.assertTrue(d.is_status("validate", "NO_INPUT"))
        self.assertFalse(d.is_valid())
        d.put(7)
        self.assertTrue(d.is_valid())
        d.validate()
        self.assertTrue(d.is_status("validate", "OK"))
        self.assertTrue(d.is_valid())


    def test_validate_with_input(self):
        i = self.LoggingInputProc()
        d = DataNode(int, i, "a")
        self.assertTrue(d.is_status("validate", "NIL"))
        self.assertFalse(d.is_valid())
        i.reset_log()
        d.validate()
        self.assertTrue(d.is_status("validate", "OK"))
        self.assertEqual(i.get_log(), ["validate"])
        self.assertTrue(d.is_valid())
        self.assertEqual(d.get(), 0)


    def test_validate_with_input_fail(self):
        i = self.FailingInputProc("OK", "INPUT_VALIDATION_FAIL")
        d = DataNode(int, i, "a")
        self.assertTrue(d.is_status("validate", "NIL"))
        self.assertFalse(d.is_valid())
        d.validate()
        self.assertTrue(d.is_status("validate", "INPUT_VALIDATION_FAIL"))
        self.assertFalse(d.is_valid())
        d.put(7)
        self.assertTrue(d.is_valid())
        d.validate()
        self.assertTrue(d.is_status("validate", "OK"))
        self.assertTrue(d.is_valid())


    def test_invalidate(self):
        d = DataNode(int)
        d.put(7)
        self.assertTrue(d.is_valid())
        d.invalidate()
        self.assertFalse(d.is_valid())


    def test_invalidate_outputs(self):
        d = DataNode(int)
        o1 = self.LoggingOutputProc()
        d.add_output(o1)
        o2 = self.LoggingOutputProc()
        d.add_output(o2)
        d.invalidate()
        self.assertEqual(o1.get_log(), [])
        self.assertEqual(o2.get_log(), [])
        d.put(7)
        self.assertTrue(d.is_valid())
        d.invalidate()
        self.assertFalse(d.is_valid())
        self.assertEqual(o1.get_log(), [("invalidate", d)])
        self.assertEqual(o2.get_log(), [("invalidate", d)])


class Test_ProcNode(unittest.TestCase):

    class LoggingInputData(Logger, InputData):

        __type: type

        def __init__(self, data_type: type) -> None:
            Logger.__init__(self)
            self.__type = data_type
        
        @status()
        def add_output(self, output: OutputProc) -> None:
            self._set_status("add_output", "OK")
            self.log("add_output", output)

        @status()
        def validate(self) -> None:
            self._set_status("validate", "OK")
            self.log("validate")

        def get_type(self) -> type:
            return self.__type

        def is_valid(self) -> bool:
            return True

        @status()
        def get(self) -> Any:
            self._set_status("get", "OK")
            self.log("get")
            return 0


    class FailingInputData(InputData):
        
        __type: type
        __validate_status: str

        def __init__(self, data_type: type, validate_status: str) -> None:
            super().__init__()
            self.__type = data_type
            self.__validate_status = validate_status
        
        @status()
        def add_output(self, output: OutputProc) -> None:
            self._set_status("add_output", "OK")

        @status()
        def validate(self) -> None:
            self._set_status("validate", self.__validate_status)

        def get_type(self) -> type:
            return self.__type

        def is_valid(self) -> bool:
            return False

        @status()
        def get(self) -> Any:
            self._set_status("get", "INVALID_DATA")
            return None

    
    class LoggingOutputData(Logger, OutputData):

        __type: type

        def __init__(self, data_type: type) -> None:
            Logger.__init__(self)
            self.__type = data_type
        
        @status()
        def put(self, value: Any) -> None:
            self._set_status("put", "OK")
            self.log("put", value)

        def invalidate(self) -> None:
            self.log("invalidate")

        def get_type(self) -> type:
            return self.__type


    class FailingOutputData(OutputData):

        __type: type

        def __init__(self, data_type: type) -> None:
            super().__init__()
            self.__type = data_type
        
        @status()
        def put(self, value: Any) -> None:
            self._set_status("put", "INCOMPATIBLE_TYPE")

        def invalidate(self) -> None:
            pass

        def get_type(self) -> type:
            return self.__type


    class LoggingData(LoggingInputData, LoggingOutputData):
        
        def __init__(self, data_type: type) -> None:
            Test_ProcNode.LoggingInputData.__init__(self, data_type)
            Test_ProcNode.LoggingOutputData.__init__(self, data_type)


    def MakeLoggingProc(self, inputs: dict[str, type],
            outputs: dict[str, type],
            logger: Logger) -> Type[Procedure]:
        
        class LoggingProc(Procedure):

            @classmethod
            def get_input_types(cls) -> dict[str, type]:
                logger.log("get_input_types")
                return inputs

            @classmethod
            def create(cls, inputs: dict[str, type]) -> "LoggingProc":
                logger.log("create", inputs)
                return cls(inputs, outputs)

            def __init__(self, inputs: dict[str, type],
                    outputs: dict[str, type]) -> None:
                super().__init__()
            
            @final
            @status()
            def put(self, name: str, value: Any) -> None:
                logger.log("put", name, value)
                self._set_status("put", "OK")

            @final
            def get_output_types(self) -> dict[str, type]:
                logger.log("get_output_types")
                return outputs
            
            @final
            @status()
            def get(self, name: str) -> Any:
                logger.log("get", name)
                self._set_status("get", "OK")
                return 0
        
        return LoggingProc

    def MakeFailingProc(self, inputs: dict[str, type],
            outputs: dict[str, type],
            put_status: str, get_status: str) -> Type[Procedure]:
        
        class FailingProc(Procedure):

            @classmethod
            def get_input_types(cls) -> dict[str, type]:
                return inputs

            @classmethod
            def create(cls, inputs: dict[str, type]) -> "FailingProc":
                return cls(inputs, outputs)

            def __init__(self, inputs: dict[str, type],
                    outputs: dict[str, type]) -> None:
                super().__init__()
            
            @final
            @status()
            def put(self, name: str, value: Any) -> None:
                self._set_status("put", put_status)

            @final
            def get_output_types(self) -> dict[str, type]:
                return outputs
            
            @final
            @status()
            def get(self, name: str) -> Any:
                self._set_status("get", get_status)
                return 0
        
        return FailingProc

    
    def test_init(self):
        pl = Logger()
        a = self.LoggingInputData(int)
        b = self.LoggingInputData(str)
        p = ProcNode(self.MakeLoggingProc(
            {"a": int, "b": str}, {"c": float, "d": complex}, pl),
            {"a": a, "b": b})
        self.assertTrue(p.is_status("init", "OK"))
        self.assertEqual(p.get_output_types(), {"c": float, "d": complex})
        self.assertEqual(pl.get_log(), [
            "get_input_types",
            ("create", {"a": int, "b": str}),
            "get_output_types",
        ])
        self.assertTrue(p.is_status("init", "OK"))
        self.assertEqual(a.get_log(), [("add_output", p)])
        self.assertEqual(b.get_log(), [("add_output", p)])

    
    def test_init_fail(self):
        pl = Logger()
        a = self.LoggingInputData(int)
        b = self.LoggingInputData(float)
        p = ProcNode(self.MakeLoggingProc({"a": int, "b": str}, {}, pl),
            {"a": a, "c": b})
        self.assertTrue(p.is_status("init", "INCOMPATIBLE_INPUT_SLOTS"))
        
        p = ProcNode(self.MakeLoggingProc({"a": int, "b": str}, {}, pl),
            {"a": a, "b": b})
        self.assertTrue(p.is_status("init", "INCOMPATIBLE_INPUT_TYPES"))

        p = ProcNode(self.MakeLoggingProc({"a": int, "b": str}, {}, pl),
            {"a": a})
        self.assertTrue(p.is_status("init", "INCOMPLETE_INPUT"))


    def test_add_output(self):
        i = self.LoggingData(int)
        pl = Logger()
        p = ProcNode(self.MakeLoggingProc({"i": int}, {"a": int, "b": str}, pl),
            {"i": i})
        a = self.LoggingOutputData(int)
        b = self.LoggingOutputData(float)
        self.assertTrue(p.is_status("add_output", "NIL"))
        p.add_output("a", a)
        self.assertTrue(p.is_status("add_output", "OK"))
        p.add_output("foo", b)
        self.assertTrue(p.is_status("add_output", "INVALID_SLOT_NAME"))
        p.add_output("i", b)
        self.assertTrue(p.is_status("add_output", "INVALID_SLOT_NAME"))
        p.add_output("a", b)
        self.assertTrue(p.is_status("add_output", "SLOT_OCCUPIED"))
        p.add_output("b", i)
        self.assertTrue(p.is_status("add_output", "ALREADY_LINKED"))
        p.add_output("b", a)
        self.assertTrue(p.is_status("add_output", "ALREADY_LINKED"))
        p.add_output("b", b)
        self.assertTrue(p.is_status("add_output", "INCOMPATIBLE_TYPE"))


    def test_invalidate(self):
        a = self.LoggingInputData(int)
        b = self.LoggingInputData(int)
        pl = Logger()
        p = ProcNode(self.MakeLoggingProc(
            {"a": int}, {"c": int, "d": int}, pl),
            {"a": a})
        c = self.LoggingOutputData(int)
        d = self.LoggingOutputData(int)
        p.add_output("c", c)
        p.add_output("d", d)
        c.reset_log()
        d.reset_log()
        pl.reset_log()
        self.assertTrue(p.is_status("invalidate", "NIL"))
        p.invalidate(b)
        self.assertTrue(p.is_status("invalidate", "NOT_INPUT"))
        p.invalidate(a)
        self.assertTrue(p.is_status("invalidate", "OK"))
        self.assertEqual(pl.get_log(), [])
        self.assertEqual(c.get_log(), ["invalidate"])
        self.assertEqual(d.get_log(), ["invalidate"])


    def test_validate(self):
        a = self.LoggingInputData(int)
        b = self.LoggingInputData(int)
        pl = Logger()
        p = ProcNode(self.MakeLoggingProc(
            {"a": int, "b": int}, {"c": int, "d": int}, pl),
            {"a": a, "b": b})
        c = self.LoggingOutputData(int)
        d = self.LoggingOutputData(int)
        p.add_output("c", c)
        p.add_output("d", d)
        a.reset_log()
        b.reset_log()
        c.reset_log()
        d.reset_log()
        pl.reset_log()
        self.assertTrue(p.is_status("validate", "NIL"))
        p.validate()
        self.assertTrue(p.is_status("validate", "OK"))
        self.assertEqual(a.get_log(), ["validate", "get"])
        self.assertEqual(b.get_log(), ["validate", "get"])
        self.assertEqual(set(pl.get_log()[:2]),
            {("put", "a", 0), ("put", "b", 0)})
        self.assertEqual(set(pl.get_log()[2:]),
            {("get", "c"), ("get", "d")})
        self.assertEqual(c.get_log(), [("put", 0)])
        self.assertEqual(d.get_log(), [("put", 0)])

        a.reset_log()
        b.reset_log()
        c.reset_log()
        d.reset_log()
        pl.reset_log()
        p.validate()
        self.assertTrue(p.is_status("validate", "OK"))
        self.assertEqual(a.get_log(), [])
        self.assertEqual(b.get_log(), [])
        self.assertEqual(set(pl.get_log()),
            {("get", "c"), ("get", "d")})
        self.assertEqual(c.get_log(), [("put", 0)])
        self.assertEqual(d.get_log(), [("put", 0)])

        p.invalidate(a)
        a.reset_log()
        b.reset_log()
        c.reset_log()
        d.reset_log()
        pl.reset_log()
        p.validate()
        self.assertTrue(p.is_status("validate", "OK"))
        self.assertEqual(a.get_log(), ["validate", "get"])
        self.assertEqual(b.get_log(), [])
        self.assertEqual(pl.get_log()[0], ("put", "a", 0))
        self.assertEqual(set(pl.get_log()[1:]),
            {("get", "c"), ("get", "d")})
        self.assertEqual(c.get_log(), [("put", 0)])
        self.assertEqual(d.get_log(), [("put", 0)])


    def test_validate_input_fail(self):
        a = self.FailingInputData(int, "NO_INPUT")
        pl = Logger()
        p = ProcNode(self.MakeLoggingProc(
            {"a": int}, {"c": int, "d": int}, pl),
            {"a": a})
        c = self.LoggingOutputData(int)
        d = self.LoggingOutputData(int)
        p.add_output("c", c)
        p.add_output("d", d)
        c.reset_log()
        d.reset_log()
        pl.reset_log()
        self.assertTrue(p.is_status("validate", "NIL"))
        p.validate()
        self.assertTrue(p.is_status("validate", "INPUT_VALIDATION_FAIL"))


    def test_validate_proc_value_fail(self):
        a = self.LoggingInputData(int)
        p = ProcNode(self.MakeFailingProc({"a": int}, {"c": int, "d": int},
                "INVALID_VALUE", "OK"),
            {"a": a})
        c = self.LoggingOutputData(int)
        d = self.LoggingOutputData(int)
        p.add_output("c", c)
        p.add_output("d", d)
        a.reset_log()
        c.reset_log()
        d.reset_log()
        self.assertTrue(p.is_status("validate", "NIL"))
        p.validate()
        self.assertTrue(p.is_status("validate", "INVALID_INPUT_VALUE"))


    def test_validate_proc_fail(self):
        for status in [
                ("INVALID_NAME", "OK"),
                ("INCOMPATIBLE_TYPE", "OK"),
                ("OK", "INVALID_NAME"),
                ("OK", "INCOMPLETE_INPUT"),
                ]:
            a = self.LoggingInputData(int)
            p = ProcNode(self.MakeFailingProc({"a": int}, {"c": int, "d": int},
                    *status),
                {"a": a})
            c = self.LoggingOutputData(int)
            d = self.LoggingOutputData(int)
            p.add_output("c", c)
            p.add_output("d", d)
            a.reset_log()
            c.reset_log()
            d.reset_log()
            self.assertTrue(p.is_status("validate", "NIL"))
            p.validate()
            self.assertTrue(p.is_status("validate", "INVALID_PROCEDURE"))

    
    def test_validate_proc_output_fail(self):
        pl = Logger()
        p = ProcNode(self.MakeLoggingProc({}, {"a": int}, pl), {})
        a = self.FailingOutputData(int)
        p.add_output("a", a)
        pl.reset_log()
        self.assertTrue(p.is_status("validate", "NIL"))
        p.validate()
        self.assertTrue(p.is_status("validate", "INVALID_PROCEDURE"))


"""
class Divmod(Procedure):
    
    __left: Optional[int]
    __right: Optional[int]
    __need_calculate: bool
    __quotient: Optional[int]
    __remainder: Optional[int]

    def __init__(self) -> None:
        super().__init__()
        self.__left = None
        self.__right = None
        self.__quotient = None
        self.__remainder = None
        self.__need_calculate = True

    @final
    @status()
    def put(self, name: str, value: Any) -> None:
        if type(value) is not int:
            self._set_status("put", "INCOMPATIBLE_TYPE")
            return
        self.__need_calculate = True
        match name:
            case "left":
                self.__left = value
                self._set_status("put", "OK")
            case "right":
                self.__right = value
                self._set_status("put", "OK")
            case _:
                self._set_status("put", "INVALID_NAME")
    
    @final
    @status()
    def get(self, name: str) -> Any:
        if self.__left is None or self.__right is None:
            self._set_status("get", "INCOMPLETE_INPUT")
            return None
        if self.__need_calculate:
            self.__quotient, self.__remainder = divmod(self.__left, self.__right)
        match name:
            case "quotient":
                self._set_status("get", "OK")
                return self.__quotient
            case "remainder":
                self._set_status("get", "OK")
                return self.__remainder
            case _:
                self._set_status("get", "INVALID_NAME")
                return None

class Test_Nodes(unittest.TestCase):

    def test_single(self):
        a = ValueNode(int)
        b = ValueNode(int)
        q = ValueNode(int)
        r = ValueNode(int)
        dm = ProcedureNode(Divmod())
        a.add_output(dm)
        a.complete_build()
        b.add_output(dm)
        b.complete_build()
        dm.add_input("left", a)
        dm.add_input("right", b)
        dm.add_output("quotient", q)
        dm.add_output("remainder", r)
        dm.complete_build()
        q.add_input(dm)
        q.complete_build()
        r.add_input(dm)
        r.complete_build()
        a.put(20)
        b.put(7)
        q.validate()
        r.validate()
        self.assertEqual(q.get(), 2)
        self.assertEqual(r.get(), 6)

    def test_chain(self):
        a = ValueNode(int)
        b = ValueNode(int)
        c = ValueNode(int)
        d = ValueNode(int)
        e = ValueNode(int)
        f = ValueNode(int)
        p1 = ProcedureNode(Divmod())
        p2 = ProcedureNode(Divmod())
        a.add_output(p1)
        a.complete_build()
        b.add_output(p1)
        b.complete_build()
        p1.add_input("left", a)
        p1.add_input("right", b)
        p1.add_output("quotient", c)
        p1.add_output("remainder", d)
        p1.complete_build()
        c.add_input(p1)
        c.add_output(p2)
        c.complete_build()
        d.add_input(p1)
        d.add_output(p2)
        d.complete_build()
        p2.add_input("left", c)
        p2.add_input("right", d)
        p2.add_output("quotient", e)
        p2.add_output("remainder", f)
        p2.complete_build()
        e.add_input(p2)
        e.complete_build()
        f.add_input(p2)
        f.complete_build()
        a.put(101)
        b.put(7)
        e.validate()
        f.validate()
        self.assertEqual(e.get(), 4)
        self.assertEqual(f.get(), 2)


class Test_Simulator(unittest.TestCase):

    def test_init(self):
        s = Simulator([
            ("a", int),
        ])
        self.assertTrue(s.is_status("init", "OK"))
        self.assertEqual(s.get_init_message(), "")

        s = Simulator([
            ("a", int),
            ("b", int),
            ("c", int),
            ("d", int),
            (Divmod(),
                {"left": "a", "right": "b"},
                {"quotient": "c", "remainder": "d"}),
        ])
        self.assertTrue(s.is_status("init", "OK"))
        self.assertEqual(s.get_init_message(), "")

        s = Simulator([
            ("a", int),
            ("b", int),
            (Divmod(),
                {"left": "a", "right": "b"},
                {"quotient": "c", "remainder": "d"}),
            ("c", int),
            ("d", int),
            (Divmod(),
                {"left": "c", "right": "d"},
                {"quotient": "e", "remainder": "f"}),
            ("e", int),
            ("f", int),
        ])
        self.assertTrue(s.is_status("init", "OK"))
        self.assertEqual(s.get_init_message(), "")

        s = Simulator([
            (Divmod(),
                {"left": int, "right": int},
                {"quotient": "c", "remainder": "d"}),
            ("c", int),
            ("d", int),
            (Divmod(),
                {"left": "c", "right": "d"},
                {"quotient": int, "remainder": int}),
        ])
        self.assertTrue(s.is_status("init", "OK"))
        self.assertEqual(s.get_init_message(), "")

        s = Simulator([
            (BlackHole(), {"foo": int}, {}),
            (BlackHole(), {"foo": int}, {}),
        ])
        self.assertTrue(s.is_status("init", "OK"))
        self.assertEqual(s.get_init_message(), "")

        s = Simulator([
            (BlackHole(), {"foo": int}, {}),
            (BlackHole(), {}, {"foo": int}),
        ])
        self.assertTrue(s.is_status("init", "OK"))
        self.assertEqual(s.get_init_message(), "")

        s = Simulator([
            ("a", int),
            ("b", int),
            ("a", str),
        ])
        self.assertTrue(s.is_status("init", "DUPLICATE_NAME"))
        self.assertEqual(s.get_init_message(), "Duplicate name: 'a'")

        s = Simulator([
            ("a", int),
            (BlackHole(),
                {"left": "c"},
                {}),
        ])
        self.assertTrue(s.is_status("init", "NAME_NOT_FOUND"))
        self.assertEqual(s.get_init_message(), "Input not found: 'left': 'c'")

        s = Simulator([
            ("a", int),
            (BlackHole(),
                {},
                {"left": "c"}),
        ])
        self.assertTrue(s.is_status("init", "NAME_NOT_FOUND"))
        self.assertEqual(s.get_init_message(), "Output not found: 'left': 'c'")

        s = Simulator([
            ("a", int),
            (BlackHole(),
                {"foo": "a", "boo": "a"},
                {}),
        ])
        self.assertTrue(s.is_status("init", "ALREADY_LINKED"))
        self.assertEqual(s.get_init_message(), "Already linked: 'boo': 'a'")

        s = Simulator([
            ("a", int),
            (BlackHole(),
                {"foo": "a"},
                {"boo": "a"}),
        ])
        self.assertTrue(s.is_status("init", "ALREADY_LINKED"))
        self.assertEqual(s.get_init_message(), "Already linked: 'boo': 'a'")

        s = Simulator([
            ("a", int),
            (BlackHole(),
                {},
                {"foo": "a", "boo": "a"}),
        ])
        self.assertTrue(s.is_status("init", "ALREADY_LINKED"))
        self.assertEqual(s.get_init_message(), "Already linked: 'boo': 'a'")

        s = Simulator([
            ("a", int),
            (BlackHole(), {}, {"foo": "a"}),
            (BlackHole(), {}, {"foo": "a"}),
        ])
        self.assertTrue(s.is_status("init", "TOO_MANY_INPUTS"))
        self.assertEqual(s.get_init_message(), "Too many inputs: 'foo': 'a'")

        s = Simulator([
            (BlackHole(), {"foo": int}, {}),
            (BlackHole(), {"foo": str}, {}),
        ])
        self.assertTrue(s.is_status("init", "AUTO_VALUE_TYPE_MISMATCH"))
        self.assertEqual(s.get_init_message(),
            "Auto value 'foo' type mismatch: <class 'str'> and <class 'int'>")


    def test_put(self):
        s = Simulator([("a", int), ("a", int)])
        self.assertTrue(s.is_status("init", "DUPLICATE_NAME"))
        self.assertTrue(s.is_status("put", "NIL"))
        s.put("a", 1)
        self.assertTrue(s.is_status("put", "INTERNAL_ERROR"))

        s = Simulator([
            ("a", int),
            ("b", int),
            (Divmod(),
                {"left": "a", "right": "b"},
                {"quotient": "c", "remainder": "d"}),
            ("c", int),
            ("d", int),
            (Divmod(),
                {"left": "c", "right": "d"},
                {"quotient": "e", "remainder": "f"}),
            ("e", int),
            ("f", int),
        ])
        self.assertTrue(s.is_status("init", "OK"))
        self.assertTrue(s.is_status("put", "NIL"))
        s.put("a", 1)
        self.assertTrue(s.is_status("put", "OK"))
        s.put("foo", 1)
        self.assertTrue(s.is_status("put", "INVALID_NAME"))
        s.put("c", 1)
        self.assertTrue(s.is_status("put", "INVALID_NAME"))


    def test_get(self):
        s = Simulator([("a", int), ("a", int)])
        self.assertTrue(s.is_status("init", "DUPLICATE_NAME"))
        self.assertTrue(s.is_status("get", "NIL"))
        s.get("a")
        self.assertTrue(s.is_status("get", "INTERNAL_ERROR"))

        s = Simulator([
            ("a", int),
            ("b", int),
            (Divmod(),
                {"left": "a", "right": "b"},
                {"quotient": "c", "remainder": "d"}),
            ("c", int),
            ("d", int),
            (Divmod(),
                {"left": "c", "right": "d"},
                {"quotient": "e", "remainder": "f"}),
            ("e", int),
            ("f", int),
        ])
        self.assertTrue(s.is_status("init", "OK"))
        self.assertTrue(s.is_status("get", "NIL"))
        s.get("foo")
        self.assertTrue(s.is_status("get", "INVALID_NAME"))
        s.get("e")
        self.assertTrue(s.is_status("get", "INCOMPLETE_INPUT"))
        s.put("a", 101)
        s.put("b", 7)
        self.assertEqual(s.get("e"), 4)
        self.assertTrue(s.is_status("get", "OK"))
        self.assertEqual(s.get("c"), 14)
        self.assertTrue(s.is_status("get", "OK"))


    def test_Nested(self):
        ddm = Simulator([
            ("a", int),
            ("b", int),
            (Divmod(),
                {"left": "a", "right": "b"},
                {"quotient": "c", "remainder": "d"}),
            ("c", int),
            ("d", int),
            (Divmod(),
                {"left": "c", "right": "d"},
                {"quotient": "e", "remainder": "f"}),
            ("e", int),
            ("f", int),
        ])
        s = Simulator([
            ("a", int),
            ("b", int),
            (ddm,
                {"a": "a", "b": "b"},
                {"e": "c", "f": "d"}),
            ("c", int),
            ("d", int),
        ])
        self.assertTrue(s.is_status("init", "OK"))
        s.put("a", 101)
        s.put("b", 7)
        self.assertEqual(s.get("c"), 4)
        self.assertTrue(s.is_status("get", "OK"))
        self.assertEqual(s.get("d"), 2)
        self.assertTrue(s.is_status("get", "OK"))
"""


if __name__ == "__main__":
    unittest.main()
