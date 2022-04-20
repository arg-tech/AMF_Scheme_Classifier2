from flask import Flask, request
import json

import os

application = Flask(__name__)
    
from app import routes
