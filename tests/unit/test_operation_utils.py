from typing import List, Optional
from dataclasses import dataclass
from scout_apm_logging.utils.operation_utils import (
    OperationDetail,
    OperationType,
    get_operation_detail,
)


@dataclass
class MockSpan:
    operation: str


@dataclass
class MockTrackedRequest:
    operation: Optional[str] = None
    active_spans: Optional[List[MockSpan]] = None


def test_operation_detail_entrypoint_attribute():
    detail = OperationDetail(name="test", type="controller")
    assert detail.entrypoint_attribute == "controller_entrypoint"


def test_get_operation_detail_from_operation_attribute():
    record = MockTrackedRequest(operation="Controller/TestController")
    result = get_operation_detail(record)
    assert result == OperationDetail(
        name="TestController", type=OperationType.CONTROLLER
    )


def test_get_operation_detail_from_spans():
    spans = [
        MockSpan(operation="Other/Operation"),
        MockSpan(operation="Job/TestJob"),
        MockSpan(operation="Controller/TestController"),
    ]
    record = MockTrackedRequest(active_spans=spans)
    result = get_operation_detail(record)
    assert result == OperationDetail(
        name="TestController", type=OperationType.CONTROLLER
    )


def test_get_operation_detail_custom_operation():
    record = MockTrackedRequest(operation="Custom/TestCustom")
    result = get_operation_detail(record)
    assert result == OperationDetail(name="TestCustom", type=OperationType.CUSTOM)


def test_get_operation_detail_unknown_prefix():
    record = MockTrackedRequest(operation="Unknown/TestUnknown")
    result = get_operation_detail(record)
    assert result is None


def test_get_operation_detail_no_operation_or_spans():
    record = MockTrackedRequest()
    result = get_operation_detail(record)
    assert result is None


def test_get_operation_detail_empty_spans():
    record = MockTrackedRequest(active_spans=[])
    result = get_operation_detail(record)
    assert result is None


def test_get_operation_detail_spans_no_match():
    spans = [
        MockSpan(operation="Other/Operation1"),
        MockSpan(operation="Other/Operation2"),
    ]
    record = MockTrackedRequest(active_spans=spans)
    result = get_operation_detail(record)
    assert result is None


def test_get_operation_detail_operation_priority():
    spans = [MockSpan(operation="Job/TestJob")]
    record = MockTrackedRequest(
        operation="Controller/TestController", active_spans=spans
    )
    result = get_operation_detail(record)
    assert result == OperationDetail(
        name="TestController", type=OperationType.CONTROLLER
    )
