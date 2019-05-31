from datetime import datetime, timedelta
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
        '🚨Gasto suspeito de Dep. {} ({}). '
        'Você pode me ajudar a verificar? '
        '{} #SerenataDeAmor'
    )

    def __init__(self, mention=False):
        self.api = twitter.Api(
            settings.TWITTER_CONSUMER_KEY,
            settings.TWITTER_CONSUMER_SECRET,
            settings.TWITTER_ACCESS_TOKEN,
            settings.TWITTER_ACCESS_SECRET
        )
        self.mention = mention
        self._message, self._reimbursement = '', None

    @property
    def queryset(self):
        kwargs = {
            'issue_date__gte': datetime.now() - timedelta(days=365 * 2),
            'issue_date__lte': datetime.now() - timedelta(days=91),
            'suspicions__meal_price_outlier': True,
            'tweet': None,
        }

        if self.mention:
            kwargs['congressperson_id__in'] = Subquery(
                SocialMedia.objects.exclude(twitter_profile='')
                .distinct('congressperson_id')
                .values_list('congressperson_id', flat=True)
            )

        queryset = Reimbursement.objects \
            .filter(**kwargs) \
            .exclude(congressperson_id=None) \
            .order_by('-issue_date')

        count = queryset.count()
        if not count:
            return queryset

        top_quartile = count // 4 or 1
        return queryset[:top_quartile]

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

        congressperson = self.reimbursement.congressperson_name
        if self.mention:
            social_media = SocialMedia.objects \
                .exclude(twitter_profile='', secondary_twitter_profile='') \
                .get(congressperson_id=self.reimbursement.congressperson_id)
            congressperson = f'@{social_media.twitter}'

        self._message = self.TEXT.format(
            congressperson,
            self.reimbursement.state,
            self.LINK.format(self.reimbursement.document_id)
        )
        return self._message

    def publish(self):
        """Post the update to Twitter's timeline."""
        tweet = self.api.PostUpdate(self.message)
        Tweet.objects.create(reimbursement=self.reimbursement, status=tweet.id)
