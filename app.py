"""Flask application for the Python Learning Lab."""

from __future__ import annotations

import os
import random
from datetime import date
from pathlib import Path

from flask import (Flask, abort, flash, redirect, render_template, request,
                   session, url_for)

from database import (create_task, delete_task, get_task, init_database,
                      list_tasks, planner_statistics, toggle_task, update_task)
from services.dice_lab import roll_dice, simulate_dice
from services.guessing_lab import (DIFFICULTIES, binary_search_steps,
                                   new_game, submit_guess)
from services.rps_lab import CHOICES, choose_opponent_move, determine_winner
from services.task_validation import MODULES, PRIORITIES, validate_task_form


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-only-change-before-production"),
        DATABASE=str(Path(app.instance_path) / "python_learning_lab.sqlite3"),
    )
    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    init_database(app.config["DATABASE"])

    @app.context_processor
    def shared_context():
        return {"year": date.today().year}

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.route("/planner", methods=["GET", "POST"])
    def planner():
        if request.method == "POST":
            values, errors = validate_task_form(request.form)
            if errors:
                return render_template(
                    "planner.html", tasks=list_tasks(app.config["DATABASE"]),
                    stats=planner_statistics(app.config["DATABASE"]),
                    modules=MODULES, priorities=PRIORITIES, errors=errors,
                    form_values=request.form, filters={},
                ), 400
            create_task(app.config["DATABASE"], values)
            flash("Assessment added to your planner.", "success")
            return redirect(url_for("planner"))

        filters = {
            "module": request.args.get("module", ""),
            "priority": request.args.get("priority", ""),
            "status": request.args.get("status", ""),
            "deadline": request.args.get("deadline", ""),
            "sort": request.args.get("sort", "due_date"),
        }
        return render_template(
            "planner.html", tasks=list_tasks(app.config["DATABASE"], filters),
            stats=planner_statistics(app.config["DATABASE"]), modules=MODULES,
            priorities=PRIORITIES, filters=filters, errors={}, form_values={},
        )

    @app.route("/planner/<int:task_id>/edit", methods=["GET", "POST"])
    def edit_task(task_id: int):
        task = get_task(app.config["DATABASE"], task_id)
        if task is None:
            abort(404)
        if request.method == "POST":
            values, errors = validate_task_form(request.form)
            if errors:
                return render_template(
                    "task_form.html", task=task, modules=MODULES,
                    priorities=PRIORITIES, errors=errors,
                    form_values=request.form,
                ), 400
            update_task(app.config["DATABASE"], task_id, values)
            flash("Assessment updated.", "success")
            return redirect(url_for("planner"))
        return render_template(
            "task_form.html", task=task, modules=MODULES,
            priorities=PRIORITIES, errors={}, form_values=dict(task),
        )

    @app.post("/planner/<int:task_id>/toggle")
    def toggle_task_route(task_id: int):
        task = toggle_task(app.config["DATABASE"], task_id)
        if task is None:
            abort(404)
        flash(
            "Assessment completed." if task["completed"] else "Assessment reopened.",
            "success",
        )
        return redirect(request.form.get("next") or url_for("planner"))

    @app.post("/planner/<int:task_id>/delete")
    def delete_task_route(task_id: int):
        if not delete_task(app.config["DATABASE"], task_id):
            abort(404)
        flash("Assessment deleted.", "success")
        return redirect(url_for("planner"))

    @app.route("/guessing", methods=["GET", "POST"])
    def guessing():
        game = session.get("guessing_game")
        if request.method == "POST":
            action = request.form.get("action")
            if action in {"start", "restart"}:
                difficulty = request.form.get("difficulty", "medium")
                if difficulty not in DIFFICULTIES:
                    difficulty = "medium"
                game = new_game(difficulty, random.randint(0, 100))
                session["guessing_game"] = game
                return redirect(url_for("guessing"))
            if action == "guess" and game and not game["finished"]:
                try:
                    guess = int(request.form.get("guess", ""))
                except ValueError:
                    flash("Enter a whole number in the remaining range.", "error")
                else:
                    game, message = submit_guess(game, guess)
                    session["guessing_game"] = game
                    flash(message, "success" if game["won"] else "info")
                return redirect(url_for("guessing"))

        comparison = None
        if game and game["finished"]:
            comparison = binary_search_steps(0, 100, game["secret"])
        return render_template(
            "guessing.html", game=game, difficulties=DIFFICULTIES,
            comparison=comparison,
        )

    @app.route("/rps", methods=["GET", "POST"])
    def rps():
        state = session.get("rps_state", {
            "history": [], "wins": 0, "losses": 0, "draws": 0,
        })
        if request.method == "POST":
            if request.form.get("action") == "reset":
                session.pop("rps_state", None)
                flash("Rock Paper Scissors statistics reset.", "success")
                return redirect(url_for("rps"))
            player = request.form.get("choice")
            mode = request.form.get("mode", "random")
            if player not in CHOICES or mode not in {"random", "adaptive"}:
                flash("Choose a valid move and opponent mode.", "error")
                return redirect(url_for("rps"))
            opponent, prediction = choose_opponent_move(
                mode, [round_["player"] for round_ in state["history"]]
            )
            result = determine_winner(player, opponent)
            counter_key = {"win": "wins", "loss": "losses", "draw": "draws"}[result]
            state[counter_key] += 1
            state["history"].append({
                "player": player, "opponent": opponent, "result": result,
                "mode": mode, "prediction": prediction,
            })
            state["history"] = state["history"][-20:]
            session["rps_state"] = state
            return redirect(url_for("rps", mode=mode))

        total = state["wins"] + state["losses"] + state["draws"]
        win_rate = round((state["wins"] / total) * 100, 1) if total else 0
        return render_template(
            "rps.html", state=state, choices=CHOICES,
            mode=request.args.get("mode", "random"), win_rate=win_rate,
        )

    @app.route("/dice", methods=["GET", "POST"])
    def dice():
        result = None
        values = {"number_of_dice": "2", "sides": "6", "simulations": "1000"}
        errors = []
        if request.method == "POST":
            values = request.form
            try:
                number_of_dice = int(values.get("number_of_dice", ""))
                sides = int(values.get("sides", ""))
                simulations = int(values.get("simulations", "1000"))
                if not 1 <= number_of_dice <= 10:
                    errors.append("Choose between 1 and 10 dice.")
                if not 2 <= sides <= 100:
                    errors.append("Choose between 2 and 100 sides per die.")
                if not 1 <= simulations <= 100_000:
                    errors.append("Choose between 1 and 100,000 simulations.")
            except ValueError:
                errors.append("Dice, sides, and simulations must be whole numbers.")
            if not errors:
                if values.get("mode") == "roll":
                    result = roll_dice(number_of_dice, sides)
                else:
                    result = simulate_dice(number_of_dice, sides, simulations)
        return render_template("dice.html", result=result, values=values, errors=errors)

    @app.errorhandler(404)
    def not_found(error):
        return render_template("404.html"), 404

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
