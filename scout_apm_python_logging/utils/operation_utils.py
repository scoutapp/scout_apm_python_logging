from typing import Optional
from dataclasses import dataclass
from scout_apm.core.tracked_request import TrackedRequest


@dataclass
class OperationDetail:
    name: str
    type: str

    @property
    def entrypoint_attribute(self) -> str:
        return f"{self.type}_entrypoint"


class OperationType:
    CONTROLLER = "controller"
    JOB = "job"
    CUSTOM = "custom"


OPERATION_PREFIXES = {
    "Controller/": OperationType.CONTROLLER,
    "Job/": OperationType.JOB,
    "Custom/": OperationType.CUSTOM,
}


def get_operation_detail(record: TrackedRequest) -> Optional[OperationDetail]:
    def extract_operation(operation: str) -> Optional[OperationDetail]:
        for prefix, op_type in OPERATION_PREFIXES.items():
            if operation.startswith(prefix):
                return OperationDetail(name=operation[len(prefix) :], type=op_type)
        return None

    # Check the operation attribute first
    operation = getattr(record, "operation", None)
    if operation:
        return extract_operation(operation)

    # Fall back to checking spans
    spans = getattr(record, "complete_spans", None) or []
    for span in reversed(spans):
        result = extract_operation(span.operation)
        if result:
            return result

    return None
