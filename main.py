from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.clock import Clock
from plyer import notification
import sqlite3
from datetime import datetime

class FarmHelperApp(App):
    def build(self):
        self.conn = sqlite3.connect('farm_helper.db')
        self.create_tables()
        self.selected_animal = None
        return self.build_main_menu()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS Animals (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS Milking (
            id INTEGER PRIMARY KEY,
            animal_id INTEGER,
            liters REAL NOT NULL,
            note TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS Feeding (
            id INTEGER PRIMARY KEY,
            animal_id INTEGER,
            amount REAL NOT NULL,
            unit TEXT NOT NULL,
            food_type TEXT NOT NULL,
            note TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS Grazing (
            id INTEGER PRIMARY KEY,
            animal_id INTEGER,
            start_time DATETIME,
            end_time DATETIME,
            duration INTEGER,
            location TEXT
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS Health (
            id INTEGER PRIMARY KEY,
            animal_id INTEGER,
            status TEXT NOT NULL,
            description TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS Reminders (
            id INTEGER PRIMARY KEY,
            action TEXT NOT NULL,
            time TEXT NOT NULL,
            repeat TEXT
        )''')
        cursor.execute("INSERT OR IGNORE INTO Animals (id, name, type) VALUES (1, 'Корова', 'Корова')")
        cursor.execute("INSERT OR IGNORE INTO Animals (id, name, type) VALUES (2, 'Теля', 'Теля')")
        self.conn.commit()

    def build_main_menu(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        animals = self.get_animals()
        animal_names = [animal[1] for animal in animals]
        self.animal_spinner = Spinner(text='Виберіть тварину', values=animal_names or ['Корова', 'Теля'])
        layout.add_widget(self.animal_spinner)

        actions = [
            ('Записати доїння', self.show_milking),
            ('Записати годування теляти', self.show_feeding_calf),
            ('Записати годування корови', self.show_feeding_cow),
            ('Записати випас', self.show_grazing),
            ('Записати стан', self.show_health),
            ('Переглянути звіт', self.show_report),
            ('Налаштування нагадувань', self.show_reminders),
            ('Додати тварину', self.add_animal)
        ]

        for text, callback in actions:
            btn = Button(text=text, size_hint=(1, 0.1))
            btn.bind(on_press=callback)
            layout.add_widget(btn)

        return layout

    def get_animals(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM Animals")
        return cursor.fetchall()

    def show_milking(self, instance):
        if not self.animal_spinner.text or self.animal_spinner.text == 'Виберіть тварину':
            self.show_popup('Помилка', 'Виберіть тварину!')
            return

        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        layout.add_widget(Label(text='Кількість молока (літри):'))
        liters_input = TextInput(multiline=False, input_filter='float')
        layout.add_widget(liters_input)
        layout.add_widget(Label(text='Примітка (необов’язково):'))
        note_input = TextInput(multiline=True)
        layout.add_widget(note_input)

        def save_milking(instance):
            liters = liters_input.text
            note = note_input.text
            if not liters or float(liters) <= 0 or float(liters) > 50:
                self.show_popup('Помилка', 'Введіть коректну кількість молока (0–50 л)')
                return
            cursor = self.conn.cursor()
            animal_id = self.get_animal_id(self.animal_spinner.text)
            cursor.execute("INSERT INTO Milking (animal_id, liters, note) VALUES (?, ?, ?)",
                          (animal_id, float(liters), note))
            self.conn.commit()
            popup.dismiss()
            self.show_popup('Успіх', 'Доїння записано!')

        save_btn = Button(text='Зберегти')
        save_btn.bind(on_press=save_milking)
        layout.add_widget(save_btn)

        popup = Popup(title='Запис доїння', content=layout, size_hint=(0.8, 0.8))
        popup.open()

    def show_feeding_calf(self, instance):
        if not self.animal_spinner.text or self.animal_spinner.text == 'Виберіть тварину':
            self.show_popup('Помилка', 'Виберіть тварину!')
            return

        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        layout.add_widget(Label(text='Кількість молока (літри):'))
        amount_input = TextInput(multiline=False, input_filter='float')
        layout.add_widget(amount_input)
        layout.add_widget(Label(text='Тип корму:'))
        food_type = Spinner(text='Молоко', values=('Молоко', 'Комбікорм', 'Трава', 'Інше'))
        layout.add_widget(food_type)
        layout.add_widget(Label(text='Примітка (необов’язково):'))
        note_input = TextInput(multiline=True)
        layout.add_widget(note_input)

        def save_feeding(instance):
            amount = amount_input.text
            if not amount or float(amount) <= 0 or float(amount) > 10:
                self.show_popup('Помилка', 'Введіть коректну кількість (0–10 л)')
                return
            cursor = self.conn.cursor()
            animal_id = self.get_animal_id(self.animal_spinner.text)
            cursor.execute("INSERT INTO Feeding (animal_id, amount, unit, food_type, note) VALUES (?, ?, ?, ?, ?)",
                          (animal_id, float(amount), 'л', food_type.text, note_input.text))
            self.conn.commit()
            popup.dismiss()
            self.show_popup('Успіх', 'Годування теляти записано!')

        save_btn = Button(text='Зберегти')
        save_btn.bind(on_press=save_feeding)
        layout.add_widget(save_btn)

        popup = Popup(title='Годування теляти', content=layout, size_hint=(0.8, 0.8))
        popup.open()

    def show_feeding_cow(self, instance):
        if not self.animal_spinner.text or self.animal_spinner.text == 'Виберіть тварину':
            self.show_popup('Помилка', 'Виберіть тварину!')
            return

        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        layout.add_widget(Label(text='Кількість:'))
        amount_input = TextInput(multiline=False, input_filter='float')
        layout.add_widget(amount_input)
        layout.add_widget(Label(text='Одиниця виміру:'))
        unit = Spinner(text='кг', values=('кг', 'л', 'відра'))
        layout.add_widget(unit)
        layout.add_widget(Label(text='Тип корму:'))
        food_type = Spinner(text='Сіно', values=('Сіно', 'Овес', 'Буряк', 'Інше'))
        layout.add_widget(food_type)

        def save_feeding(instance):
            amount = amount_input.text
            if not amount or float(amount) <= 0:
                self.show_popup('Помилка', 'Введіть коректну кількість')
                return
            cursor = self.conn.cursor()
            animal_id = self.get_animal_id(self.animal_spinner.text)
            cursor.execute("INSERT INTO Feeding (animal_id, amount, unit, food_type) VALUES (?, ?, ?, ?)",
                          (animal_id, float(amount), unit.text, food_type.text))
            self.conn.commit()
            popup.dismiss()
            self.show_popup('Успіх', 'Годування корови записано!')

        save_btn = Button(text='Зберегти')
        save_btn.bind(on_press=save_feeding)
        layout.add_widget(save_btn)

        popup = Popup(title='Годування корови', content=layout, size_hint=(0.8, 0.8))
        popup.open()

    def show_grazing(self, instance):
        if not self.animal_spinner.text or self.animal_spinner.text == 'Виберіть тварину':
            self.show_popup('Помилка', 'Виберіть тварину!')
            return

        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.grazing_animal_id = self.get_animal_id(self.animal_spinner.text)

        def start_grazing(instance):
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO Grazing (animal_id, start_time) VALUES (?, ?)",
                          (self.grazing_animal_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            self.conn.commit()
            self.show_popup('Успіх', 'Випас розпочато!')

        def end_grazing(instance):
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, start_time FROM Grazing WHERE animal_id = ? AND end_time IS NULL",
                          (self.grazing_animal_id,))
            grazing = cursor.fetchone()
            if grazing:
                start_time = datetime.strptime(grazing[1], '%Y-%m-%d %H:%M:%S')
                end_time = datetime.now()
                duration = int((end_time - start_time).total_seconds() / 60)
                cursor.execute("UPDATE Grazing SET end_time = ?, duration = ? WHERE id = ?",
                              (end_time.strftime('%Y-%m-%d %H:%M:%S'), duration, grazing[0]))
                self.conn.commit()
                self.show_popup('Успіх', f'Випас завершено! Тривалість: {duration} хвилин')
            else:
                self.show_popup('Помилка', 'Випас не розпочато!')

        start_btn = Button(text='Почати випас')
        start_btn.bind(on_press=start_grazing)
        layout.add_widget(start_btn)

        end_btn = Button(text='Завершити випас')
        end_btn.bind(on_press=end_grazing)
        layout.add_widget(end_btn)

        popup = Popup(title='Випас', content=layout, size_hint=(0.8, 0.8))
        popup.open()

    def show_health(self, instance):
        if not self.animal_spinner.text or self.animal_spinner.text == 'Виберіть тварину':
            self.show_popup('Помилка', 'Виберіть тварину!')
            return

        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        layout.add_widget(Label(text='Стан тварини:'))
        status = Spinner(text='Здорове', values=('Здорове', 'Хворе', 'Вагітне', 'Потребує ветеринара'))
        layout.add_widget(status)
        layout.add_widget(Label(text='Опис:'))
        desc_input = TextInput(multiline=True)
        layout.add_widget(desc_input)

        def save_health(instance):
            cursor = self.conn.cursor()
            animal_id = self.get_animal_id(self.animal_spinner.text)
            cursor.execute("INSERT INTO Health (animal_id, status, description) VALUES (?, ?, ?)",
                          (animal_id, status.text, desc_input.text))
            self.conn.commit()
            popup.dismiss()
            self.show_popup('Успіх', 'Стан записано!')

        save_btn = Button(text='Зберегти')
        save_btn.bind(on_press=save_health)
        layout.add_widget(save_btn)

        popup = Popup(title='Стан тварини', content=layout, size_hint=(0.8, 0.8))
        popup.open()

    def show_report(self, instance):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        cursor = self.conn.cursor()

        cursor.execute("SELECT SUM(liters) FROM Milking WHERE timestamp LIKE ?",
                      (datetime.now().strftime('%Y-%m-%d') + '%',))
        milk_today = cursor.fetchone()[0] or 0
        layout.add_widget(Label(text=f'Молока сьогодні: {milk_today} л'))

        cursor.execute("SELECT SUM(amount), food_type FROM Feeding WHERE timestamp LIKE ? GROUP BY food_type",
                      (datetime.now().strftime('%Y-%m-%d') + '%',))
        feeding = cursor.fetchall()
        for amount, food in feeding:
            layout.add_widget(Label(text=f'Годування: {food} - {amount}'))

        popup = Popup(title='Звіт за сьогодні', content=layout, size_hint=(0.8, 0.8))
        popup.open()

    def show_reminders(self, instance):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        layout.add_widget(Label(text='Дія:'))
        action = Spinner(text='Доїння', values=('Доїння', 'Годування теляти', 'Годування корови'))
        layout.add_widget(action)
        layout.add_widget(Label(text='Час (HH:MM):'))
        time_input = TextInput(multiline=False, text='18:00')
        layout.add_widget(time_input)

        def save_reminder(instance):
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO Reminders (action, time, repeat) VALUES (?, ?, ?)",
                          (action.text, time_input.text, 'щодня'))
            self.conn.commit()
            Clock.schedule_once(lambda dt: self.notify(action.text, time_input.text), 1)
            popup.dismiss()
            self.show_popup('Успіх', 'Нагадування встановлено!')

        save_btn = Button(text='Зберегти')
        save_btn.bind(on_press=save_reminder)
        layout.add_widget(save_btn)

        popup = Popup(title='Нагадування', content=layout, size_hint=(0.8, 0.8))
        popup.open()

    def add_animal(self, instance):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        layout.add_widget(Label(text='Ім’я тварини:'))
        name_input = TextInput(multiline=False)
        layout.add_widget(name_input)
        layout.add_widget(Label(text='Тип:'))
        type_input = Spinner(text='Корова', values=('Корова', 'Теля'))
        layout.add_widget(type_input)

        def save_animal(instance):
            if not name_input.text:
                self.show_popup('Помилка', 'Введіть ім’я тварини!')
                return
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO Animals (name, type) VALUES (?, ?)",
                          (name_input.text, type_input.text))
            self.conn.commit()
            self.animal_spinner.values = [animal[1] for animal in self.get_animals()]
            popup.dismiss()
            self.show_popup('Успіх', 'Тварину додано!')

        save_btn = Button(text='Зберегти')
        save_btn.bind(on_press=save_animal)
        layout.add_widget(save_btn)

        popup = Popup(title='Додати тварину', content=layout, size_hint=(0.8, 0.8))
        popup.open()

    def get_animal_id(self, name):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM Animals WHERE name = ?", (name,))
        return cursor.fetchone()[0]

    def notify(self, action, time):
        notification.notify(title='Ферма Помічник', message=f'Час для: {action} о {time}')

    def show_popup(self, title, message):
        layout = BoxLayout(orientation='vertical', padding=10)
        layout.add_widget(Label(text=message))
        close_btn = Button(text='OK', size_hint=(1, 0.2))
        layout.add_widget(close_btn)
        popup = Popup(title=title, content=layout, size_hint=(0.6, 0.4))
        close_btn.bind(on_press=popup.dismiss)
        popup.open()

if __name__ == '__main__':
    FarmHelperApp().run()
