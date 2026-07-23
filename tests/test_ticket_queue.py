import unittest
from unittest.mock import Mock, patch

from utils import ticket_queue


class FakeExecutor:
    def __init__(self):
        self.submissions = []

    def submit(self, func, *args, **kwargs):
        self.submissions.append((func, args, kwargs))
        return "future"


class TicketQueueTests(unittest.TestCase):
    def setUp(self):
        ticket_queue.reset_ticket_queue_status()

    def test_enqueue_ticket_job_submits_job_to_executor(self):
        executor = FakeExecutor()
        job = Mock(return_value="ok")

        with patch.object(ticket_queue, "_executor", executor):
            result = ticket_queue.enqueue_ticket_job("test ticket", job, "ABC123", copies=1)

        self.assertEqual(result, "future")
        submitted_func, args, kwargs = executor.submissions[0]
        self.assertIs(submitted_func, ticket_queue._run_ticket_job)
        self.assertEqual(args, ("test ticket", job, ("ABC123",), {"copies": 1}))
        self.assertEqual(kwargs, {})

    def test_successful_job_updates_status(self):
        executor = FakeExecutor()
        job = Mock(return_value="ok")

        with patch.object(ticket_queue, "_executor", executor):
            ticket_queue.enqueue_ticket_job("success ticket", job)

        submitted_func, args, kwargs = executor.submissions[0]
        result = submitted_func(*args, **kwargs)
        status = ticket_queue.get_ticket_queue_status()

        self.assertEqual(result, "ok")
        self.assertEqual(status["last_submitted_description"], "success ticket")
        self.assertEqual(status["last_started_description"], "success ticket")
        self.assertEqual(status["last_success_description"], "success ticket")
        self.assertEqual(status["submitted"], 1)
        self.assertEqual(status["succeeded"], 1)
        self.assertEqual(status["failed"], 0)

    def test_run_ticket_job_logs_exception_without_raising(self):
        def failing_job():
            raise RuntimeError("printer offline")

        with self.assertLogs(ticket_queue.logger, level="ERROR") as logs:
            result = ticket_queue._run_ticket_job("test ticket", failing_job, (), {})

        self.assertIsNone(result)
        self.assertIn("Ticket job failed: test ticket", "\n".join(logs.output))

    def test_failing_job_updates_status_without_raising(self):
        def failing_job():
            raise RuntimeError("printer offline")

        with self.assertLogs(ticket_queue.logger, level="ERROR"):
            result = ticket_queue._run_ticket_job("failed ticket", failing_job, (), {})

        status = ticket_queue.get_ticket_queue_status()
        self.assertIsNone(result)
        self.assertEqual(status["last_started_description"], "failed ticket")
        self.assertEqual(status["last_failure_description"], "failed ticket")
        self.assertEqual(status["last_failure_error"], "printer offline")
        self.assertEqual(status["succeeded"], 0)
        self.assertEqual(status["failed"], 1)

    def test_get_ticket_queue_status_returns_copy(self):
        executor = FakeExecutor()

        with patch.object(ticket_queue, "_executor", executor):
            ticket_queue.enqueue_ticket_job("copy ticket", Mock())

        status = ticket_queue.get_ticket_queue_status()
        status["submitted"] = 999
        status["last_submitted_description"] = "mutated"

        fresh_status = ticket_queue.get_ticket_queue_status()
        self.assertEqual(fresh_status["submitted"], 1)
        self.assertEqual(fresh_status["last_submitted_description"], "copy ticket")


if __name__ == "__main__":
    unittest.main()
