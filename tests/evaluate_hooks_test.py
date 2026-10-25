import _thread
import contextlib
import threading

import pytest

import jsonata
from jsonata import jexception

# infinite tail recursion: the trampoline keeps the Python stack flat,
# so only the timebox can stop it
RUNAWAY = "$f := function($n){$f($n+1)}; $f(0)"


@contextlib.contextmanager
def watchdog(seconds=5):
    # fail the test instead of hanging if the timebox does not fire;
    # interrupt_main works on every platform, unlike SIGALRM. The
    # KeyboardInterrupt must be caught here, or pytest aborts the session
    timer = threading.Timer(seconds, _thread.interrupt_main)
    timer.start()
    try:
        yield
    except KeyboardInterrupt:
        raise AssertionError("expression was not stopped by the timebox")
    finally:
        timer.cancel()


class TestEvaluateHooks:

    def test_callbacks_called_for_each_node(self):
        expression = jsonata.Jsonata("a + b")
        frame = expression.create_frame()
        entries = []
        exits = []
        frame.set_evaluate_entry_callback(lambda expr, input, env: entries.append(expr.type))
        frame.set_evaluate_exit_callback(lambda expr, input, env, res: exits.append(res))
        assert expression.evaluate({"a": 1, "b": 2}, frame) == 3
        assert entries == ["binary", "path", "name", "path", "name"]
        assert exits[-1] == 3

    def test_callbacks_inherited_by_nested_frames(self):
        expression = jsonata.Jsonata("($x := 1; $f := function($y){$x + $y}; $f(2))")
        frame = expression.create_frame()
        types = []
        frame.set_evaluate_entry_callback(lambda expr, input, env: types.append(expr.type))
        assert expression.evaluate(None, frame) == 3
        # nodes inside the block and the lambda body are evaluated in nested frames
        assert "block" in types and "lambda" in types and types.count("variable") >= 2

    def test_bindings_frame_without_hooks_keeps_expression_hooks(self):
        expression = jsonata.Jsonata("(" + RUNAWAY + ")", timeout=200)
        frame = expression.create_frame()
        frame.bind("unused", 1)
        with watchdog(), pytest.raises(jexception.JException) as err:
            expression.evaluate(None, frame)
        assert err.value.error == "D1012"

    def test_hooks_are_not_variables(self):
        expression = jsonata.Jsonata("$__evaluate_entry")
        frame = expression.create_frame()
        frame.set_evaluate_entry_callback(lambda expr, input, env: None)
        assert expression.evaluate(None, frame) is None

    def test_expression_cannot_disable_timeout(self):
        expression = jsonata.Jsonata(
            "($__evaluate_entry := $undefined; $__evaluate_exit := $undefined; " + RUNAWAY + ")",
            timeout=200)
        with watchdog(), pytest.raises(jexception.JException) as err:
            expression.evaluate(None)
        assert err.value.error == "D1012"

    def test_expression_cannot_disable_stack_limit(self):
        expression = jsonata.Jsonata(
            "($__evaluate_entry := $undefined; $__evaluate_exit := $undefined;"
            " $f := function($n){$n = 0 ? 0 : 1 + $f($n-1)}; $f(1000))",
            stack=50)
        with watchdog(), pytest.raises(jexception.JException) as err:
            expression.evaluate(None)
        assert err.value.error == "D1011"
