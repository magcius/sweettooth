
import xapian

from django.conf import settings
from django.db.models import signals

from extensions.models import Extension, ExtensionVersion

def index_extension(extension):
    if extension.latest_version is None:
        return

    db = xapian.WritableDatabase(settings.XAPIAN_DB_PATH, xapian.DB_CREATE_OR_OPEN)

    termgen = xapian.TermGenerator()
    termgen.set_stemmer(xapian.Stem("en"))

    doc = xapian.Document()
    termgen.set_document(doc)

    termgen.index_text(extension.name, 10)
    termgen.index_text(extension.uuid)
    termgen.index_text(extension.description)

    doc.set_data(str(extension.pk))

    idterm = "Q%s" % (extension.pk,)
    doc.add_boolean_term(idterm)
    db.replace_document(idterm, doc)

def delete_extension(extension):
    db = xapian.WritableDatabase(settings.XAPIAN_DB_PATH, xapian.DB_CREATE_OR_OPEN)
    idterm = "Q%s" % (extension.pk,)
    db.delete_document(idterm)


def post_extension_save_handler(instance, **kwargs):
    index_extension(instance)
signals.post_save.connect(post_extension_save_handler, sender=Extension)

def post_extension_delete_handler(instance, **kwargs):
    delete_extension(instance)
signals.post_delete.connect(post_extension_delete_handler, sender=Extension)

def post_version_save_handler(instance, **kwargs):
    index_extension(instance.extension)
signals.post_save.connect(post_version_save_handler, sender=ExtensionVersion)

def enquire(querystring):
    try:
        db = xapian.Database(settings.XAPIAN_DB_PATH)
    except xapian.DatabaseOpeningError:
        return None

    qp = xapian.QueryParser()
    qp.set_stemming_strategy(qp.STEM_SOME)
    qp.set_stemmer(xapian.Stem("en"))
    qp.set_database(db)

    enquire = xapian.Enquire(db)
    enquire.set_query(qp.parse_query(querystring))

    return db, enquire
