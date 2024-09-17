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

    # Check the current span first
    current_span = record.current_span()
    if current_span:
        return extract_operation(current_span.operation)

    # If no current span, check the last completed span
    if record.complete_spans:
        last_span = record.complete_spans[-1]
        return extract_operation(last_span.operation)

    # If no spans at all, fall back to the record's operation attribute
    # TODO this may never happen and could possibly be removed
    operation = getattr(record, "operation", None)
    if operation:
        return extract_operation(operation)

    return None
