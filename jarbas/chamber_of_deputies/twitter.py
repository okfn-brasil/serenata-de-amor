from random import choice

import twitter
from django.db.models import Subquery
from django.conf import settings

from jarbas.chamber_of_deputies.models import Reimbursement, SocialMedia, Tweet


class Twitter:
    """Twitter target. Maintains the logic for posting suspicious
    reimbursements in a Twitter account.
    """

    LINK = 'https://jarbas.serenata.ai/layers/#/documentId/{}'
    TEXT = (
        '🚨Gasto suspeito de Dep. @{} ({}). '
        'Você pode me ajudar a verificar? '
        '{} #SerenataDeAmor na @CamaraDeputados'
    )

    def __init__(self):
        self.api = twitter.Api(
            settings.TWITTER_CONSUMER_KEY,
            settings.TWITTER_CONSUMER_SECRET,
            settings.TWITTER_ACCESS_TOKEN,
            settings.TWITTER_ACCESS_SECRET
        )
        self._message, self._reimbursement = '', None

    @property
    def queryset(self):
        last_term = Reimbursement.objects \
            .exclude(term=None) \
            .distinct('term') \
            .order_by('-term') \
            .values_list('term', flat=True) \
            .first()

        congressperson_ids_with_twitter = Subquery(
            SocialMedia.objects.exclude(twitter_profile='')
            .distinct('congressperson_id')
            .values_list('congressperson_id', flat=True)
        )

        kwargs = {
            'issue_date__year__gte': last_term,
            'term': last_term,
            'suspicions__meal_price_outlier': True,
            'tweet': None,
            'congressperson_id__in': congressperson_ids_with_twitter
        }

        return Reimbursement.objects.filter(**kwargs)

    @property
    def reimbursement(self):
        if self._reimbursement:
            return self._reimbursement

        if not self.queryset.exists():
            return None

        self._reimbursement = choice(self.queryset)
        return self.reimbursement

    @property
    def message(self):
        """Proper tweet message for the given reimbursement."""
        if self._message:
            return self._message

        try:
            social_media = SocialMedia.objects \
                .exclude(twitter_profile='', secondary_twitter_profile='') \
                .get(congressperson_id=self.reimbursement.congressperson_id)
        except (SocialMedia.DoesNotExist, SocialMedia.MultipleObjectsReturned):
            msg = 'No social account found for congressperson_id {}'
            print(msg.format(self.reimbursement.congressperson_id))
            return None

        self._message = self.TEXT.format(
            social_media.twitter,
            self.reimbursement.state,
            self.LINK.format(self.reimbursement.document_id)
        )
        return self.message

    def publish(self):
        """Post the update to Twitter's timeline."""
        tweet = self.api.PostUpdate(self.message)
        Tweet.objects.create(reimbursement=self.reimbursement, status=tweet.id)
