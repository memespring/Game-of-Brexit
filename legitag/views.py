from flask import request, render_template, send_from_directory, abort, redirect, url_for, flash
from flask.ext.security import login_required, current_user
from legitag import app, models, forms
from mongoengine import DoesNotExist
import random
import requests

@app.route('/')
def about():
    edit_count = models.EditCount.objects.order_by('-count')
    return render_template('about.html', edit_count=edit_count, menu_item='tools')

@app.route('/proxy')
def proxy():
    try:
        url = request.args.get('url', False)
        if url:
            if url.startswith('http://publications.europa.eu') or url.startswith('http://eur-lex.europa.eu'):
                headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

                html =  requests.get(url, headers=headers).content

                return html
            else:
                abort(404)
        else:
            abort(404)
    except:
        abort(404)

@app.route('/question', methods=['GET', 'POST'])
def legislation():

    total = models.Legislation.objects.count()
    if total == 0:
        abort(404)

    questions = [
        {'key': 'policy', 'question': 'Name some policy areas this might cover', 'examples': 'eg farming, workers rights, groundwater management'},
        {'key': 'user', 'question': 'Name some people or organisations this might it affect', 'examples': 'eg farmer, supermarket, police, car manufacturer'},
        {'key': 'devolvable', 'question': 'Could this reasonably be devolved to Scotland, Wales, Northern Ireland or London?', 'examples': None, 'choices': [('yes', 'Yes'), ('no', 'No')]},
        {'key': 'important', 'question': 'Does this sound important?', 'examples': None, 'choices': [('yes', 'Yes'), ('no', 'No')]},
        {'key': 'ministers-should-decide', 'question': 'Should ministers be able to make decisions about this without a vote in parliament?', 'examples': None, 'choices': [('yes', 'Yes'), ('no', 'No')]},
    ]

    if request.method == 'GET':

        #random legislation
        legislation = models.Legislation.objects[random.randint(0, total-1):].first()

        #populate form
        question = random.choice(questions)
        if 'choices' in question:
            form = forms.OptionForm()
            form.values.choices = question['choices']
        else:
            form = forms.TagForm()
        form.legislation_id.data = legislation.id
        form.key.data = question['key']
        form.values.label.text = question['question']
        form.values.description = question['examples']

    if request.method == 'POST':
        form = forms.TagForm(request.form)
        legislation = models.Legislation.objects.get(id=form.legislation_id.data)
        if form.validate():

            # policy areas
            for item in form.values.data.split(','):
                if item.strip() != '':
                    tag = models.Tag()
                    tag.key = form.key.data
                    tag.value = item.strip().lower()
                    legislation.append_tag(tag)
            try:
                if current_user.is_authenticated:
                    legislation.save(current_user, "Added tags")
                else:
                    legislation.save(None, "Added tags")
            except:
                pass

        return redirect(url_for('legislation'))

    return render_template('legislation.html', legislation=legislation, form=form, menu_item='tools')

@app.route('/tags')
def tags():
    tags = models.Legislation.objects.distinct('_tags')
    tags.sort(key=lambda x: x.key)

    return render_template('tags.html', menu_item='tags', tags=tags)

@app.route('/tags/<tag>')
def tag_browse(tag):
    tag_split = tag.split(':')
    legislations = models.Legislation.objects(_tags__key=tag_split[0], _tags__value=tag_split[1])
    return render_template('tags_browse.html', menu_item='tags', tag=tag, legislations=legislations)

@app.route('/search')
def search():
    query = request.args.get('q', False)
    legislations = []
    if query:
        legislations = models.Legislation.objects.search_text(query).order_by('$text_score')
    return render_template('search.html', menu_item='search', legislations=legislations, query=query)