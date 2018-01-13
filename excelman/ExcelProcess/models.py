from django.db import models
import datetime
# Create your models here.
class Document(models.Model):
	docfile = models.FileField(upload_to="documents/")
	pub_date = models.DateTimeField('date published')
	def __str__(self):
		#d = datetime.datetime.strptime(str(self.pub_date, '%Y-%m-%d')
		d=self.pub_date.strftime('%d-%m-%Y %H:%M')
		return str(d)
	def was_published_recently(self):
		return self.pub_date >= timezone.now() - datetime.timedelta(days=1)