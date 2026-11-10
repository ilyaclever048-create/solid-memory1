import sys
import sqlite3
import csv
import os
from tkinter import (Tk, Frame, Label, Entry, Button, Text, Scrollbar,
                     Listbox, END, messagebox, Toplevel, StringVar,
                     OptionMenu, VERTICAL, HORIZONTAL, BOTH, X, Y, LEFT, RIGHT, BOTTOM)

DB_NAME = "tasks.db"
PRIORITY_LEVELS = ["Низкий", "Средний", "Высокий"]
STATUS_LEVELS = ["В процессе", "Выполнено", "Отложено"]
CATEGORIES = ["Работа", "Личное", "Учеба", "Общее"]


class DatabaseManager:

    def __init__(self, db_name=DB_NAME):
        self.db_name = db_name
        self.connection = None
        self.cursor = None
        self.initialize_database()

    def initialize_database(self):
        self.connection = sqlite3.connect(self.db_name)
        self.cursor = self.connection.cursor()

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                priority TEXT DEFAULT 'Средний',
                status TEXT DEFAULT 'В процессе',
                category TEXT DEFAULT 'Общее'
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        """)

        for category in CATEGORIES:
            try:
                self.cursor.execute("INSERT INTO categories (name) VALUES (?)", (category,))
            except sqlite3.IntegrityError:
                pass

        self.connection.commit()

    def add_task(self, title, description, priority, status, category):
        self.cursor.execute(
            "INSERT INTO tasks (title, description, priority, status, category) VALUES (?, ?, ?, ?, ?)",
            (title, description, priority, status, category)
        )
        self.connection.commit()
        return self.cursor.lastrowid

    def get_all_tasks(self):
        self.cursor.execute("SELECT * FROM tasks ORDER BY id DESC")
        return self.cursor.fetchall()

    def update_task(self, task_id, title, description, priority, status, category):
        self.cursor.execute(
            "UPDATE tasks SET title=?, description=?, priority=?, status=?, category=? WHERE id=?",
            (title, description, priority, status, category, task_id)
        )
        self.connection.commit()

    def delete_task(self, task_id):
        self.cursor.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        self.connection.commit()

    def export_to_csv(self, filename):
        tasks = self.get_all_tasks()
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['ID', 'Название', 'Описание', 'Приоритет', 'Статус', 'Категория'])
            for task in tasks:
                writer.writerow(task)

    def close(self):
        if self.connection:
            self.connection.close()


class AddTaskWindow(Toplevel):

    def __init__(self, parent, task_data=None):
        super().__init__(parent)
        self.task_data = task_data
        self.result = None
        self.title("Редактирование задачи" if task_data else "Новая задача")
        self.geometry("400x450")
        self.init_ui()

        if task_data:
            self.fill_form(task_data)

    def init_ui(self):
        main_frame = Frame(self)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

        Label(main_frame, text="Название:").pack(anchor="w")
        self.title_entry = Entry(main_frame, width=40)
        self.title_entry.pack(fill=X, pady=(0, 10))

        Label(main_frame, text="Описание:").pack(anchor="w")
        self.desc_text = Text(main_frame, height=5, width=40)
        self.desc_text.pack(fill=X, pady=(0, 10))

        frame_priority = Frame(main_frame)
        frame_priority.pack(fill=X, pady=5)
        Label(frame_priority, text="Приоритет:").pack(side=LEFT)
        self.priority_var = StringVar(value=PRIORITY_LEVELS[1])
        OptionMenu(frame_priority, self.priority_var, *PRIORITY_LEVELS).pack(side=RIGHT)

        frame_status = Frame(main_frame)
        frame_status.pack(fill=X, pady=5)
        Label(frame_status, text="Статус:").pack(side=LEFT)
        self.status_var = StringVar(value=STATUS_LEVELS[0])
        OptionMenu(frame_status, self.status_var, *STATUS_LEVELS).pack(side=RIGHT)

        frame_category = Frame(main_frame)
        frame_category.pack(fill=X, pady=5)
        Label(frame_category, text="Категория:").pack(side=LEFT)
        self.category_var = StringVar(value=CATEGORIES[3])
        OptionMenu(frame_category, self.category_var, *CATEGORIES).pack(side=RIGHT)

        btn_frame = Frame(main_frame)
        btn_frame.pack(pady=20)
        Button(btn_frame, text="Сохранить", command=self.save).pack(side=LEFT, padx=5)
        Button(btn_frame, text="Отмена", command=self.destroy).pack(side=LEFT, padx=5)

    def fill_form(self, task_data):
        self.title_entry.insert(0, task_data[1])
        self.desc_text.insert("1.0", task_data[2] or "")
        self.priority_var.set(task_data[3])
        self.status_var.set(task_data[4])
        self.category_var.set(task_data[5])

    def save(self):
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showwarning("Ошибка", "Введите название задачи")
            return

        self.result = {
            'title': title,
            'description': self.desc_text.get("1.0", "end-1c"),
            'priority': self.priority_var.get(),
            'status': self.status_var.get(),
            'category': self.category_var.get()
        }
        self.destroy()


class MainWindow(Tk):

    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.title("Менеджер задач v1.0")
        self.geometry("900x600")
        self.init_ui()
        self.load_tasks()

    def init_ui(self):
        menu_bar = Frame(self, bd=1, relief="raised")
        menu_bar.pack(fill=X)

        Button(menu_bar, text="Файл -> Экспорт CSV", command=self.export_to_csv).pack(side=LEFT, padx=5)
        Button(menu_bar, text="Справка -> О программе", command=self.show_about).pack(side=LEFT, padx=5)

        control_frame = Frame(self)
        control_frame.pack(fill=X, padx=10, pady=5)

        Button(control_frame, text="Добавить задачу", command=self.add_task).pack(side=LEFT, padx=2)
        Button(control_frame, text="Редактировать", command=self.edit_task).pack(side=LEFT, padx=2)
        Button(control_frame, text="Удалить", command=self.delete_task).pack(side=LEFT, padx=2)
        Button(control_frame, text="Обновить", command=self.load_tasks).pack(side=LEFT, padx=2)

        list_frame = Frame(self)
        list_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)

        columns = ('ID', 'Название', 'Описание', 'Приоритет', 'Статус', 'Категория')
        self.task_list = Listbox(list_frame, selectmode="browse")
        scrollbar_y = Scrollbar(list_frame, orient=VERTICAL, command=self.task_list.yview)
        scrollbar_x = Scrollbar(list_frame, orient=HORIZONTAL, command=self.task_list.xview)

        self.task_list.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        self.task_list.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar_y.pack(side=RIGHT, fill=Y)
        scrollbar_x.pack(side=BOTTOM, fill=X)

        header_text = f"{columns[0]:<5} | {columns[1]:<20} | {columns[2]:<30} | {columns[3]:<10} | {columns[4]:<15} | {columns[5]}"
        self.header_label = Label(list_frame, text=header_text, font=("Consolas", 9), anchor="w")
        self.header_label.place(relx=0, rely=0, relwidth=1)

        self.status_label = Label(self, text="Готово к работе", bd=1, relief="sunken", anchor="w")
        self.status_label.pack(fill=X, side=BOTTOM)

    def load_tasks(self):
        self.task_list.delete(0, END)
        tasks = self.db_manager.get_all_tasks()

        for task in tasks:
            line = f"{task[0]:<5} | {task[1]:<20} | {task[2][:30]:<30} | {task[3]:<10} | {task[4]:<15} | {task[5]}"
            self.task_list.insert(END, line)

        self.status_label.config(text=f"Загружено задач: {len(tasks)}")

    def get_selected_task_id(self):
        selection = self.task_list.curselection()
        if not selection:
            messagebox.showwarning("Ошибка", "Выберите задачу")
            return None

        selected_text = self.task_list.get(selection[0])
        try:
            return int(selected_text.split('|')[0].strip())
        except:
            return None

    def add_task(self):
        dialog = AddTaskWindow(self)
        self.wait_window(dialog)

        if dialog.result:
            data = dialog.result
            self.db_manager.add_task(
                data['title'],
                data['description'],
                data['priority'],
                data['status'],
                data['category']
            )
            self.load_tasks()
            messagebox.showinfo("Успех", "Задача добавлена!")

    def edit_task(self):
        task_id = self.get_selected_task_id()
        if not task_id:
            return

        tasks = self.db_manager.get_all_tasks()
        task_data = next((t for t in tasks if t[0] == task_id), None)

        if task_data:
            dialog = AddTaskWindow(self, task_data)
            self.wait_window(dialog)

            if dialog.result:
                data = dialog.result
                self.db_manager.update_task(
                    task_id,
                    data['title'],
                    data['description'],
                    data['priority'],
                    data['status'],
                    data['category']
                )
                self.load_tasks()
                messagebox.showinfo("Успех", "Задача обновлена!")

    def delete_task(self):
        task_id = self.get_selected_task_id()
        if not task_id:
            return

        if messagebox.askyesno("Подтверждение", "Удалить выбранную задачу?"):
            self.db_manager.delete_task(task_id)
            self.load_tasks()
            messagebox.showinfo("Успех", "Задача удалена!")

    def export_to_csv(self):
        filename = "tasks_export.csv"
        try:
            self.db_manager.export_to_csv(filename)
            messagebox.showinfo("Успех", f"Задачи экспортированы в {filename}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка экспорта: {str(e)}")

    def show_about(self):
        messagebox.showinfo("О программе",
                            "Менеджер задач v1.0\n\n"
                            "Простое приложение для управления задачами\n"
                            "Разработано с использованием tkinter и SQLite")

    def on_closing(self):
        self.db_manager.close()
        self.destroy()


def main():
    app = MainWindow()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()