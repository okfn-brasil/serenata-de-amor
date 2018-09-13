import twitter

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

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

    def __init__(self, congressperson_ids_with_twitter):
        self.credentials = (
            settings.TWITTER_CONSUMER_KEY,
            settings.TWITTER_CONSUMER_SECRET,
            settings.TWITTER_ACCESS_TOKEN,
            settings.TWITTER_ACCESS_SECRET
        )
        self.reimbursement = Reimbursement.objects \
            .next_tweet(congressperson_ids_with_twitter)
        self._message = ''

    @property
    def message(self):
        """Proper tweet message for the given reimbursement."""
        if self._message:
            return self._message

        try:
            social_media = SocialMedia.objects \
                .get(congressperson_id=self.reimbursement.congressperson_id)
        except (ObjectDoesNotExist, SocialMedia.MultipleObjectsReturned):
            return None

        profile = social_media.twitter_profile or \
            social_media.secondary_twitter_profile
        if not profile:
            return None

        self._message = self.TEXT.format(
            profile,
            self.reimbursement.state,
            self.LINK.format(self.reimbursement.document_id)
        )
        return self.message

    def publish(self):
        """Post the update to Twitter's timeline."""
        if not self.reimbursement:
            return None

        api = twitter.Api(*self.credentials)
        tweet = api.PostUpdate(self.message)
        Tweet.objects.create(reimbursement=self.reimbursement, status=tweet.id)
