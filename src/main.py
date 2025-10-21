from controllers.account_controller import UserController
from models.accounts import UserCreate

def main():
    testuser = UserCreate("yakiitory", "steveneugenioebreo@gmail.com",
                          "helloworld", "Steven", "Ebreo", "12345", "male", "Adult")
    testcontroller = UserController()
    testcontroller.create(testuser)

if __name__ == "__main__":
    main()