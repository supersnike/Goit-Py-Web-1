import pickle
from datetime import datetime, timedelta
from collections import UserDict
from abc import ABC, abstractmethod

class Field:  # Базовый класс полей записи.
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field):  # Класс хранения имени контакта. Обязательное поле.
    def __init__(self, name):
        if not name:
            raise ValueError("Name must not be empty.")
        super().__init__(name)

class Phone(Field):  # Класс хранения номера телефона. Проверяет телефон (10 цифр).
    def __init__(self, phone):
        if not phone.isdigit() or len(phone) != 10:
            raise ValueError("Phone number must have 10 digits.")
        super().__init__(phone)

class Birthday(Field):  # Класс хранения даты рождения.
    def __init__(self, value):
        try:
            self.value = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

class Record:  # Класс хранения информации о контакте. Имя и список телефонов.
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        for ph in self.phones:
            if ph.value == phone:
                self.phones.remove(ph)

    def edit_phone(self, old_phone, new_phone):
        phone_exists = False
        for p in self.phones:
            if p.value == old_phone:
                phone_exists = True
                break

        if not phone_exists:
            raise ValueError("Phone number to edit does not exist.")

        if not new_phone.isdigit() or len(new_phone) != 10:
            raise ValueError("New phone number must be a 10-digit number.")

        for ph in self.phones:
            if ph.value == old_phone:
                ph.value = new_phone

    def find_phone(self, phone):
        for ph in self.phones:
            if ph.value == phone:
                return ph
        return None

    def __str__(self):
        birthday_str = str(self.birthday.value.strftime("%d.%m.%Y")) if self.birthday else 'Not specified'
        return f"Contact name: {self.name.value}, phones: {'; '.join(p.value for p in self.phones)}, birthday: {birthday_str}"

class AddressBook(UserDict):  # Класс хранения и управления записями .
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]
        else:
            raise ValueError("Name not found")

    def get_upcoming_birthdays(self):
        today = datetime.today().date()
        upcoming_birthdays = []
        for user in self.data.values():
            if user.birthday:
                birthday_this_year = datetime(today.year, user.birthday.value.month, user.birthday.value.day).date()
                if birthday_this_year < today:
                    continue
                elif (birthday_this_year - today).days < 7:
                    if birthday_this_year.weekday() == 5:  # Суббота
                        birthday_this_year += timedelta(days=2)  # Перенос на понедельник
                    elif birthday_this_year.weekday() == 6:  # Воскресенье
                        birthday_this_year += timedelta(days=1)  # Перенос на понедельник
                    user_info = {"name": user.name.value, "congratulation_date": birthday_this_year.strftime("%d.%m.%Y")}
                    upcoming_birthdays.append(user_info)
        return upcoming_birthdays

class UserView(ABC):
    @abstractmethod
    def show_message(self, message: str):
        pass

    @abstractmethod
    def show_contacts(self, contacts: list):
        pass

    @abstractmethod
    def show_help(self):
        pass

class ConsoleView(UserView):
    def show_message(self, message: str):
        print(message)

    def show_contacts(self, contacts: list):
        for contact in contacts:
            print(contact)

    def show_help(self):
        print("Available commands:")
        print("  add <name> <phone>            - Add a new contact")
        print("  change <name> <new_phone>     - Change phone number of a contact")
        print("  phone <name>                  - Show phone number of a contact")
        print("  all                           - Show all contacts")
        print("  add-birthday <name> <birthday> - Add birthday to a contact (format DD.MM.YYYY)")
        print("  show-birthday <name>          - Show birthday of a contact")
        print("  birthdays                     - Show upcoming birthdays")
        print("  help                          - Show this help message")
        print("  close/exit                    - Exit the program")

def input_error(func):  # Функция-декоратор обработки исключений.
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError:
            return "This command cannot be executed."
        except ValueError:
            return "Give me name and phone please."
        except IndexError:
            return "There is no such information."
        except Exception as e:
            return f"Error: {e}"
    return inner

@input_error
def add_birthday(args, book, view):
    name, birthday = args
    try:
        record = book.find(name)
        if record:
            record.add_birthday(birthday)
            view.show_message(f"Birthday added for {name}.")
        else:
            view.show_message(f"Contact {name} not found.")
    except ValueError as e:
        view.show_message(str(e))

@input_error
def show_birthday(args, book, view):
    name = args[0]
    record = book.find(name)
    if record and record.birthday:
        view.show_message(f"{name}'s birthday: {record.birthday.value}")
    elif record and not record.birthday:
        view.show_message(f"{name} does not have a birthday specified.")
    else:
        view.show_message(f"Contact {name} not found.")

@input_error
def birthdays(args, book, view):
    upcoming_birthdays = book.get_upcoming_birthdays()
    if upcoming_birthdays:
        view.show_message("Upcoming birthdays:")
        for record in upcoming_birthdays:
            view.show_message(f"The congratulation date for {record['name']} is {record['congratulation_date']}")
    else:
        view.show_message("No upcoming birthdays.")

def parse_input(user_input):  # Парсинг ввода.
    if not user_input.strip():
        return "", []
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, args

def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()    

# Main function
def main():
    book = load_data()  
    view = ConsoleView()
    view.show_message("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        if command == "":
            continue

        if command in ["close", "exit"]:
            view.show_message("Good bye!")
            save_data(book) 
            break

        elif command == "hello":
            view.show_message("How can I help you?")

        elif command == "add":
            if len(args) != 2:
                view.show_message("Invalid number of arguments.")
                continue
            name, phone = args
            if not phone.isdigit() or len(phone) != 10:
                view.show_message("Phone number must be a 10-digit number.")
                continue
            record = Record(name)
            record.add_phone(phone)
            book.add_record(record)
            view.show_message(f"Added new contact: {name} - {phone}")

        elif command == "change":
            if len(args) != 2:
                view.show_message("Invalid number of arguments.")
                continue
            name, new_phone = args
            record = book.find(name)
            if record:
                if not new_phone.isdigit() or len(new_phone) != 10:
                    view.show_message("New phone number must be a 10-digit number.")
                    continue
                record.edit_phone(record.phones[0].value, new_phone)
                view.show_message(f"Phone number changed for {name}.")
            else:
                view.show_message(f"Contact {name} not found.")

        elif command == "phone":
            if len(args) != 1:
                view.show_message("Invalid number of arguments.")
                continue
            name = args[0]
            record = book.find(name)
            if record:
                view.show_message(f"Phone number for {name}: {record.phones[0]}")
            else:
                view.show_message(f"Contact {name} not found.")

        elif command == "all":
            contacts = [str(record) for record in book.data.values()]
            view.show_contacts(contacts)

        elif command == "add-birthday":
            if len(args) != 2:
                view.show_message("Invalid number of arguments.")
                continue
            add_birthday(args, book, view)

        elif command == "show-birthday":
            if len(args) != 1:
                view.show_message("Invalid number of arguments.")
                continue
            show_birthday(args, book, view)

        elif command == "birthdays":
            birthdays(args, book, view)

        elif command == "help":
            view.show_help()

        else:
            view.show_message("Invalid command. Type 'help' to see available commands.")

if __name__ == "__main__":
    main()
