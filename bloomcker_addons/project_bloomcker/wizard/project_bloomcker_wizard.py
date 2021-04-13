
import time
import logging
import base64
#from xml.dom import minidom
from lxml import etree
from copy import deepcopy

from odoo import api, fields, models, _

# import xml.etree.ElementTree as ET



from xml.dom import minidom

from datetime import date, datetime, timedelta

from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
DATE_LENGTH = len(date.today().strftime(DATE_FORMAT))
DATETIME_LENGTH = len(datetime.now().strftime(DATETIME_FORMAT))

_logger = logging.getLogger(__name__)

import xml.etree.ElementTree as ET


class ProjectBloomckerWizard(models.TransientModel):
    _name = "project.bloomcker.wizard"