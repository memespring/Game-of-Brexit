from datetime import datetime
from legitag import db
from flask.ext.security import UserMixin, RoleMixin, login_required
import re

class Role(db.Document, RoleMixin):
    name = db.StringField(max_length=80, unique=True)
    description = db.StringField(max_length=255)

class User(db.Document, UserMixin):
    name = db.StringField(max_length=255)
    email = db.StringField(max_length=255)
    password = db.StringField(max_length=255)
    active = db.BooleanField(default=True)
    confirmed_at = db.DateTimeField()
    roles = db.ListField(db.ReferenceField(Role), default=[])

class EditCount(db.Document):
    user = db.ReferenceField(User)
    count = db.IntField(required=True)

class Edit(db.EmbeddedDocument):
    user = db.ReferenceField(User, required=False)
    description = db.StringField(max_length=255)
    occured_at = db.DateTimeField(default=datetime.now, required=True)

class Tag(db.EmbeddedDocument):
    key = db.StringField(max_length=100, required=True)
    value = db.StringField(max_length=255, required=True)

class Legislation(db.Document):
    title = db.StringField(required=True)
    original_url = db.URLField(required=False, unique=True)
    html_url = db.URLField(required=False)
    pdf_url = db.URLField(required=False)
    created_at = db.DateTimeField(default=datetime.now, required=True)
    updated_at = db.DateTimeField(default=datetime.now, required=True)
    _tags = db.EmbeddedDocumentListField(Tag)
    _edits = db.EmbeddedDocumentListField(Edit)

    meta = {'indexes': [
    {'fields': ['$title'],
     'default_language': 'english',
     'weights': {'title': 10}
    }
    ]}

    @property
    def tags(self):
        return self._tags

    @property
    def edits(self):
        return self._edits

    @property
    def friendly_title(self):
        result = self.title
        result = result.replace("(Text with EEA relevance)", "")
        result = result.replace("Text with EEA relevance", "")
        result = re.sub("and amending Regulation.*?No.[0-9]+\/[0-9]+", "", result)
        
        key_phrases = [
            'type approval of',
            'laying down a',
            'establishing additional',
            'establishing for [1-2][0-9][0-9][0-9] the',
            'establishing an',
            'establishing a',
            'under the',
            'name entered in',
            'registration of a name in the',
            'entering a name in',
            'establishing the Community',
            'establishing the',
            'entry of a name in',
            'imposing a',
            'approving',
            'determining the',
            'determining a',
            'laying down',
            'relating to',
            'providing for',
            'on the',
            'on the special',
            'concerning',
            'as regards the',
            'as regards',
            'as concerns',
            'in respect of',
            'laying down specific rules on',
            'amending Regulation (\(EU\)|\(EEC\)) No.?[0-9]+\/[0-9]+ to',
            'amending Regulation',
            'making',
            'fixing',
            'adjusting',
            'setting',
            'imposing',
            'prohibiting',
            'implementing',
            'supplementing'
        ]

        for phrase in key_phrases:
            result = re.sub("^(Commission|Council|Commission Delegated)( Implementing)? Regulation.*%s" % phrase, "", result)    
          

        result = re.sub("Annexes .*? on ", "", result)
        result = re.sub(" \( \)", "", result)
        result = re.sub("of [1-9][1-9]?.*?[1-2][0-9][0-9][0-9]", "", result)
        result = re.sub("(\(EC\)|\(EEC\)) No.?[0-9]+\/[0-9]+ ", "", result)
        result = re.sub("(Council|Commission ) Regulation (\(EU\)|\(EU\)) No.?[0-9]+\/[0-9]+", "", result)
        result = re.sub("(Council|Commission) Regulation of [0-9][0-9]?.*?[0-9][0-9][0-9][0-9]", "", result)
        
        # result = re.sub("of 21.January.2013.fixing.for.2013", "", result)

         
        result = re.sub("Regulation No.[0-9]+ of the Economic Commission for Europe of the United Nations (\(UN\/ECE\)|\(UNECE\))", "", result)
        result = re.sub("Regulation of the European Parliament and of the Council.*?regards the ", "", result)
        result = re.sub("Regulation.*?of the European Parliament and of the Council.*?amending", "", result)
        result = re.sub("Regulation.*?of the European Central Bank.*?concerning the ", "", result)
        result = re.sub("Regulation.*?of the European Parliament and of the Council.*?laying down ", "", result)
        result = re.sub("Regulation.*?amending Regulation on", "", result)
        result = re.sub("Regulation.*?of the Commission of .*[0-9][0-9][0-9][0-9]", "", result)
        result = re.sub("Implementing Regulation \(EU\).*with regard to ", "", result)
        result = re.sub("(Directive|Regulation).*?of the European Parliament and of the Council with regard to", "", result)
        result = re.sub("amending.*?to Regulation of the European Parliament and the Council as regards", "", result)
        

        result = result.strip()
        if len(result) > 1:
            result = result[0].upper() + result[1:]
        return result

    def save(self, user=None, description=None, *args, **kwargs):

        # add to history
        if user:
            user_db = User.objects.get(id=user.get_id())
            edit = Edit(user=user_db, description=description)
        else:
            edit = Edit(user=None, description=description)
        self._edits.append(edit)

        self.updated_at = datetime.now

        super(Legislation, self).save(*args, **kwargs)

    def append_tag(self, new_tag):
        found = False
        for tag in self.tags:
            if tag.key == new_tag.key and tag.value == new_tag.value:
                found = True
        if not found:
            self._tags.append(new_tag)
