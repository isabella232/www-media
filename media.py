#!/usr/bin/env python3

from email.utils import parsedate_to_datetime
from locale import LC_ALL, setlocale
from urllib.request import urlopen
from xml.etree import ElementTree

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


def get_news():
    tree = ElementTree.parse(
        urlopen(
            'https://kozeagroup.wordpress.com/category/kozea-media/feed/'))
    news = []
    for item in tree.find('channel').findall('item'):
        date = parsedate_to_datetime(item.find('pubDate').text)
        entry = {
            'title': item.find('title').text,
            'description': item.find('description').text,
            'link': item.find('link').text,
            'isodate': date.strftime('%Y-%m-%d'),
            'date': date.strftime('%d %B %Y')
        }
        image = item.find(
            'media:thumbnail',
            namespaces={'media': 'http://search.yahoo.com/mrss/'})
        if image is not None:
            entry['image'] = image.attrib['url']
        news.append(entry)
    return news


@app.route('/')
@app.route('/<page>')
def page(page='index'):
    extra = {'news': get_news()[:2]} if page == 'index' else {}
    try:
        return render_template('{}.html'.format(page), page=page, **extra)
    except jinja2.exceptions.TemplateNotFound:
        abort(404)


@app.route('/robots.txt')
def robots():
    return Response('User-agent: *\nDisallow: \n', mimetype='text/plain')


@app.route('/news')
def news():
    return render_template('news.html', news=get_news(), page='news')


@app.route('/quotation', methods=['POST'])
def quotation():
    if all(request.form.get(key) for key in (
           'type', 'need', 'email', 'phone')):
        return contact()
    return page('quotation')


def send_mail(subject, html):
    message = {
        'to': [{'email': 'media@kozea.fr'}],
        'subject': subject,
        'from_email': 'media@kozea.fr',
        'html': html,
    }
    if app.debug:
        print(subject, message)
    else:
        mandrill.Mandrill(MANDRILL_KEY).messages.send(message=message)


@app.route('/download_whitepaper', methods=['POST'])
def download_whitepaper():
    html = '<br>'.join([
        'Nom : %s' % request.form.get('name', ''),
        'Email : %s' % request.form.get('email', ''),
        'Téléphone : %s' % request.form.get('phone', '')])
    send_mail('Téléchargement du livre blanc', html)
    flash('Nous vous remercions pour votre téléchargement.')
    return redirect(url_for('static', filename='documents/livre-blanc.pdf'))


@app.route('/contact', methods=['POST'])
def contact():
    html = '<br>'.join([
        'Nom : %s' % request.form.get('name', ''),
        'Email : %s' % request.form.get('email', ''),
        'Téléphone : %s' % request.form.get('phone', ''),
        'Message : %s' % request.form.get('message', ''),
        'Type de contact : %s' % request.form.get('type', ''),
        'Besoin : %s' % request.form.get('need', '')])
    send_mail('Contact', html)
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
