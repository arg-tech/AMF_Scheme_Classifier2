from flask import redirect, request, jsonify
from . import application
from app.classifier import Classifier
import json

application.config["DATA"] = "data/"


@application.route('/schemes_clsf', methods=['GET', 'POST'])
def amf_schemes():
    if request.method == 'POST':
        f = request.files['file']
        f.save(f.filename)
        ff = open(f.filename, 'r')
        data = json.load(ff)
        c = Classifier()
        result = c.identify_schemes(c, data)
    
    return jsonify(result)
