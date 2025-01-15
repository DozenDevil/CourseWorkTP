from flask import render_template


def render_index(images):
    return render_template('index.html', images=images)
