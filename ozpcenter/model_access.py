"""
Model (data) access methods

Should support caches. Basically stuff like:

data = cache.get('stuff')
if data is None:
    data = list(Stuff.objects.all())
    cache.set('stuff', data)
return data

Think about Listing queries: must support private apps and classification
levels, which are user dependent. Possible keys:
storefront:org1:max_classification_level


Read https://docs.djangoproject.com/en/1.8/topics/cache/
"""
import logging
import re

from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
import ozpcenter.models as models

# Get an instance of a logger
logger = logging.getLogger('ozp-center')

def make_keysafe(key):
	"""
	given an input string, make it lower case and remove all non alpha-numeric
	characters so that it will be safe to use as a cache keyname

	TODO: check for max length (250 chars by default for memcached)
	"""
	return re.sub(r'\W+', '', key).lower()


def get_storefront(username):
	"""
	Returns data for /storefront api invocation including:
		* featured listings (max=12?)
		* recent (new) listings (max=24?)
		* most popular listings (max=36?)

	NOTE: think about adding Bookmark status to this later on

	TODO: how to deal with fact that many users will have different access
	controls, making this key fairly inefficient

	Key: storefront:<org_names>:<max_classification_level>
	"""
	user = models.Profile.objects.get(username=username)
	orgs = ''
	for i in user.organizations.all():
		orgs += '%s_' % i.title
	orgs_key = make_keysafe(orgs)
	access_control_key = make_keysafe(user.access_control.title)

	key = 'storefront:%s:%s' % (orgs_key, access_control_key)
	data = cache.get(key)
	if data is None:
		try:
			# get featured listings
			featured_listings = models.Listing.objects.for_user(username).filter(
				is_featured=True,
				)[:12]

			# get recent listings
			recent_listings = models.Listing.objects.for_user(username).order_by(
				'approved_date').filter(
				)[:24]

			# get most popular listings via a weighted average
			most_popular_listings = models.Listing.objects.for_user(username).order_by(
				'avg_rate').filter(
				)[:36]

			data = {
				'featured': featured_listings,
				'recent': recent_listings,
				'most_popular': most_popular_listings
			}

			cache.set(key, data)
		except Exception as e:
			return {'error': True, 'msg': 'Error getting storefront: %s' % str(e)}
	return data


def get_metadata():
	"""
	Returns metadata including:
		* categories
		* organizations (agencies)
		* listing types
		* intents
		* contact types

	Key: metadata
	"""
	key = 'metadata'
	data = cache.get(key)
	if data is None:
		try:
			data = {}
			data['categories'] = models.Category.objects.all().values(
				'title', 'description')
			data['listing_types'] = models.ListingType.objects.all().values(
				'title', 'description')
			data['agencies'] = models.Agency.objects.all().values(
				'title', 'short_name', 'icon_url')
			data['contact_types'] = models.ContactType.objects.all().values(
				'name', 'required')
			data['intents'] = models.Intent.objects.all().values(
				'action', 'media_type', 'label', 'icon')

			cache.set(key, data)
		except Exception as e:
			return {'error': True, 'msg': 'Error getting metadata: %s' % str(e)}
	return data











