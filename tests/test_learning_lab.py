"""Core logic, persistence, and route tests for Python Learning Lab."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from app import create_app
from database import (create_task, delete_task, get_task, init_database,
                      list_tasks, planner_statistics, toggle_task, update_task)
from services.dice_lab import theoretical_distribution
from services.guessing_lab import binary_search_steps, new_game, submit_guess
from services.rps_lab import (choose_opponent_move, determine_winner,
                              predict_next_choice)


class LogicTests(unittest.TestCase):
    def test_two_six_sided_dice_distribution(self):
        distribution = theoretical_distribution(2, 6)
        self.assertAlmostEqual(sum(distribution.values()), 1.0)
        self.assertAlmostEqual(distribution[2], 1 / 36)
        self.assertAlmostEqual(distribution[7], 6 / 36)
        self.assertAlmostEqual(distribution[12], 1 / 36)

    def test_other_dice_shapes_are_exact(self):
        distribution = theoretical_distribution(3, 4)
        self.assertEqual(set(distribution), set(range(3, 13)))
        self.assertAlmostEqual(distribution[3], 1 / 64)
        self.assertAlmostEqual(distribution[12], 1 / 64)

    def test_rps_winner_rules(self):
        self.assertEqual(determine_winner("rock", "scissors"), "win")
        self.assertEqual(determine_winner("paper", "scissors"), "loss")
        self.assertEqual(determine_winner("paper", "paper"), "draw")

    def test_rps_frequency_and_transition_prediction(self):
        self.assertEqual(predict_next_choice(["rock", "rock", "paper"]), "rock")
        history = ["rock", "paper", "rock", "paper", "rock"]
        self.assertEqual(predict_next_choice(history), "paper")
        move, prediction = choose_opponent_move("adaptive", history)
        self.assertEqual(prediction, "paper")
        self.assertEqual(move, "scissors")

    def test_random_opponent_uses_injected_chooser(self):
        move, prediction = choose_opponent_move(
            "random", ["rock"], chooser=lambda choices: "paper"
        )
        self.assertEqual(move, "paper")
        self.assertIsNone(prediction)

    def test_guessing_range_narrows_without_counting_invalid_guess(self):
        game = new_game("medium", 73)
        game, _ = submit_guess(game, 50)
        self.assertEqual((game["low"], game["high"]), (51, 100))
        self.assertEqual(game["guesses"], [50])
        game, message = submit_guess(game, 20)
        self.assertEqual(game["guesses"], [50])
        self.assertIn("51", message)
        game, _ = submit_guess(game, 80)
        self.assertEqual((game["low"], game["high"]), (51, 79))

    def test_binary_search_finds_target_in_seven_steps_or_fewer(self):
        for target in range(101):
            steps = binary_search_steps(0, 100, target)
            self.assertEqual(steps[-1]["guess"], target)
            self.assertLessEqual(len(steps), 7)


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        temp_root = Path(".local-tmp")
        temp_root.mkdir(exist_ok=True)
        self.temp = TemporaryDirectory(dir=temp_root)
        self.database = str(Path(self.temp.name) / "test.sqlite3")
        init_database(self.database)
        self.values = {
            "title": "Probability worksheet",
            "description": "Complete questions 1–10",
            "module": "Maths for Data Science",
            "due_date": "2027-01-20",
            "priority": "High",
        }

    def tearDown(self):
        self.temp.cleanup()

    def test_create_read_update_toggle_and_delete(self):
        task_id = create_task(self.database, self.values)
        task = get_task(self.database, task_id)
        self.assertEqual(task["title"], self.values["title"])
        self.assertEqual(task["completed"], 0)

        changed = {**self.values, "title": "Updated worksheet", "priority": "Low"}
        self.assertTrue(update_task(self.database, task_id, changed))
        self.assertEqual(get_task(self.database, task_id)["title"], "Updated worksheet")
        self.assertEqual(toggle_task(self.database, task_id)["completed"], 1)
        self.assertEqual(toggle_task(self.database, task_id)["completed"], 0)
        self.assertTrue(delete_task(self.database, task_id))
        self.assertIsNone(get_task(self.database, task_id))

    def test_filter_sort_and_statistics(self):
        create_task(self.database, self.values)
        create_task(self.database, {
            **self.values, "title": "Python lab", "module": "Computer Programming",
            "due_date": "2027-01-10", "priority": "Low",
        })
        high_first = list_tasks(self.database, {"sort": "priority"})
        self.assertEqual(high_first[0]["priority"], "High")
        maths = list_tasks(self.database, {"module": "Maths for Data Science"})
        self.assertEqual(len(maths), 1)
        toggle_task(self.database, high_first[0]["id"])
        stats = planner_statistics(self.database)
        self.assertEqual(stats["total"], 2)
        self.assertEqual(stats["completed"], 1)
        self.assertEqual(stats["progress"], 50)


class RouteTests(unittest.TestCase):
    def setUp(self):
        temp_root = Path(".local-tmp")
        temp_root.mkdir(exist_ok=True)
        self.temp = TemporaryDirectory(dir=temp_root)
        self.database = str(Path(self.temp.name) / "route-test.sqlite3")
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "DATABASE": self.database,
        })
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp.cleanup()

    def test_database_is_created_and_every_page_loads(self):
        self.assertTrue(Path(self.database).is_file())
        for path in ["/", "/planner", "/guessing", "/rps", "/dice"]:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)
        self.assertEqual(self.client.get("/missing").status_code, 404)

    def test_planner_validates_and_persists_tasks(self):
        invalid = self.client.post("/planner", data={})
        self.assertEqual(invalid.status_code, 400)
        response = self.client.post("/planner", data={
            "title": "AI reflection",
            "description": "Write 500 words",
            "module": "Introduction to AI",
            "due_date": "2027-02-01",
            "priority": "Medium",
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"AI reflection", response.data)
        self.assertEqual(len(list_tasks(self.database)), 1)

    def test_guessing_session_round(self):
        with self.client.session_transaction() as flask_session:
            flask_session["guessing_game"] = new_game("easy", 42)
        response = self.client.post(
            "/guessing", data={"action": "guess", "guess": "42"},
            follow_redirects=True,
        )
        self.assertIn(b"You found it", response.data)
        self.assertIn(b"Binary search for 42", response.data)

    def test_rps_and_dice_posts(self):
        rps = self.client.post(
            "/rps", data={"mode": "random", "choice": "rock"},
            follow_redirects=True,
        )
        self.assertEqual(rps.status_code, 200)
        self.assertIn(b"Recent rounds", rps.data)
        dice = self.client.post("/dice", data={
            "number_of_dice": "2", "sides": "6", "simulations": "100",
            "mode": "simulate",
        })
        self.assertEqual(dice.status_code, 200)
        self.assertIn(b"Experimental vs theoretical", dice.data)


if __name__ == "__main__":
    unittest.main()
