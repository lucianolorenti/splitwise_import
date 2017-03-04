import json
from appdirs import *
from pathlib import Path
import os
class Config:
    def __init__(self):
        self.open_config()
    def is_authorized(self):
        return self.config["access_token"] != ""
    def set_access_token(self,token):
        self.config["access_token"]=token
        self.save()
    def access_token(self):
        return self.config["access_token"]
    def save(self):
        with open(self.config_file,"w") as outfile:
            json.dump(self.config, outfile)
    def open_config(self):
        self.app_name    = "SplitWise_import"
        self.app_author  = "Luciano Lorenti"
        data_dir         = user_data_dir(self.app_name, self.app_author)
        os.makedirs(data_dir,exist_ok=True)
        self.config_file = data_dir + "/config.json"
        print(self.config_file)
        if Path(self.config_file).is_file():
            with open(self.config_file) as data_file:
                self.config = json.load(data_file)
        else:
            with open(self.config_file,"w") as outfile:
                cfg = {"access_token":""}
                json.dump(cfg, outfile)
                self.config = cfg
config = Config()
