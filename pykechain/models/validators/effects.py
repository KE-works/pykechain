from pykechain.enums import ValidatorEffectTypes
from pykechain.models.validators.validators_base import ValidatorEffect


class TextEffect(ValidatorEffect):
    effect = ValidatorEffectTypes.TEXT_EFFECT


class ErrorTextEffect(ValidatorEffect):
    """A Errortext effect, that will set a text"""
    effect = ValidatorEffectTypes.ERRORTEXT_EFFECT

    def __init__(self, json=None, text="The validation resulted in an error.", **kwargs):
        super(ErrorTextEffect, self).__init__(json=json, **kwargs)
        self.text = text

    def as_json(self):
        self._config['text'] = self.text
        return self._json


class HelpTextEffect(ValidatorEffect):
    """A Errortext effect, that will set a text"""
    effect = ValidatorEffectTypes.HELPTEXT_EFFECT

    def __init__(self, json=None, text="", **kwargs):
        super(HelpTextEffect, self).__init__(json=json, **kwargs)
        self.text = text

    def as_json(self):
        self._config['text'] = self.text
        return self._json


class VisualEffect(ValidatorEffect):
    """A visualeffect, to be processed by the frontend

    :ivar applyCss: css class to apply in case of this effect
    """
    effect = ValidatorEffectTypes.VISUALEFFECT

    def __init__(self, json=None, applyCss=None, **kwargs):
        super(VisualEffect, self).__init__(json=json, **kwargs)
        self.applyCss = applyCss or self._config.get('applyCss')

    def as_json(self):
        self._config['applyCss'] = self.applyCss
        self._json['config'] = self._config
        return self._json


class ValidVisualEffect(VisualEffect):
    def __init__(self, json=None, applyCss='valid'):
        super(__class__, self).__init__(json=json, applyCss=applyCss)


class InvalidVisualEffect(VisualEffect):
    def __init__(self, json=None, applyCss='invalid'):
        super(__class__, self).__init__(json=json, applyCss=applyCss)