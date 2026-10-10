# CLI task tracker
# Original exercise preserved from Python_mini_projects.


def view_tasks(tasks):
    if not tasks:
        print("No tasks available.")
    else:
        print("All tasks:")
        for i, task in enumerate(tasks, start=1):
            status = "Completed" if task["completed"] else "Pending"
            print(f"{i}. {task['title']} - {status}")


def display_menu():
    tasks = []
    while True:
        print("\n1. All tasks")
        print("2. Exit")
        print("3. Add task")
        print("4. Mark task as complete")
        print("5. Delete task")
        menu_choice = input("Enter your choice: ")
        if menu_choice == "1":
            view_tasks(tasks)
        elif menu_choice == "2":
            break
        elif menu_choice == "3":
            title = input("Enter task title: ").strip()
            if not title:
                print("Task title cannot be empty.")
                continue
            tasks.append({"title": title, "completed": False})
            print(f"Task '{title}' added.")
        elif menu_choice == "4":
            view_tasks(tasks)
            if not tasks:
                continue
            try:
                task_number = int(input("Enter the task number to mark as complete: "))
            except ValueError:
                print("Please enter a whole number.")
                continue
            if not 1 <= task_number <= len(tasks):
                print("That task number does not exist.")
                continue
            task_index = task_number - 1
            if tasks[task_index]["completed"]:
                print("That task is already completed.")
            else:
                tasks[task_index]["completed"] = True
                print(f"Task '{tasks[task_index]['title']}' marked as complete.")
        elif menu_choice == "5":
            view_tasks(tasks)
            if not tasks:
                continue
            try:
                task_number = int(input("Enter the task number to delete: "))
            except ValueError:
                print("Please enter a whole number.")
                continue
            if not 1 <= task_number <= len(tasks):
                print("That task number does not exist.")
                continue
            deleted_task = tasks.pop(task_number - 1)
            print(f"Task '{deleted_task['title']}' deleted.")
        else:
            print("Invalid choice. Please try again.")


display_menu()
