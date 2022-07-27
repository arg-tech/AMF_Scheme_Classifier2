from flask import redirect, request, jsonify, render_template
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
    elif request.method == 'GET':
        return render_template('index.html')
