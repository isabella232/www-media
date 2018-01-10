#!/usr/bin/env python3

from locale import LC_ALL, setlocale

import jinja2
import mandrill
from flask import (Flask, Response, abort, flash, redirect, render_template,
                   request, url_for)

app = Flask(__name__)

# Secret key doesn't have to be changed, it is only used for flash messages
app.secret_key = 'secret key'
app.config.from_envvar('WWWMEDIA_CONFIG', silent=True)

setlocale(LC_ALL, 'fr_FR')

MANDRILL_KEY = app.config.get('MANDRILL_KEY')


@app.route('/')
@app.route('/<page>')
def page(page='index'):
    try:
        return render_template('{}.html'.format(page), page=page)
    except jinja2.exceptions.TemplateNotFound:
        abort(404)


@app.route('/robots.txt')
def robots():
    return Response('User-agent: *\nDisallow: \n', mimetype='text/plain')


@app.route('/contact', methods=['POST'])
def contact():
    message = {
        'to': [{'email': 'media@kozea.fr'}],
        'subject': 'Prise de contact sur le site de Kozea Media',
        'from_email': 'media@kozea.fr',
        'html': '<br>'.join([
            'Nom : %s' % request.form.get('name', ''),
            'Email : %s' % request.form.get('email', ''),
            'Téléphone : %s' % request.form.get('phone', ''),
            'Message : %s' % request.form.get('message', ''),
            'Type de contact : %s' % request.form.get('type', ''),
            'Besoin : %s' % request.form.get('need', ''),
            'Cible : %s' % request.form.get('target', '')])}

    if app.debug:
        print(message)
    else:
        mandrill.Mandrill(MANDRILL_KEY).messages.send(message=message)

    flash(
        'Nous vous remercions pour votre demande. '
        'Notre équipe va revenir vers vous dans les plus brefs délais.')
    return redirect(url_for('page'))


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


if __name__ == '__main__':
    from sassutils.wsgi import SassMiddleware
    app.wsgi_app = SassMiddleware(app.wsgi_app, {
        'media': ('sass', 'static/css', '/static/css')})
    app.run(debug=True)
    app.run(debug=True)
