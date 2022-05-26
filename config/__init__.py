from dotenv import dotenv_values, load_dotenv

global config
load_dotenv()
config = dotenv_values('.env')