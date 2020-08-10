from pykechain.enums import ValidatorEffectTypes
from pykechain.models.validators.validators_base import ValidatorEffect


class TextEffect(ValidatorEffect):
    """A Text effect, that will set a text.

    .. versionadded:: 2.2
    """

    effect = ValidatorEffectTypes.TEXT_EFFECT

    def __init__(self, json=None, text="The validation resulted in an error.", **kwargs):
        """Construct an helptext effect.

        :param json: (optional) dict (json) object to construct the object from
        :type json: dict
        :param text: (optional) text to provide, default empty
        :type text: basestring
        :param kwargs: (optional) additional kwargs to pass down
        :type kwargs: dict
        """
        super(TextEffect, self).__init__(json=json, text=text, **kwargs)
        self.text = text

    def as_json(self):
        # type: () -> dict
        """Represent effect as JSON dict."""
        self._config['text'] = self.text
        return self._json


class ErrorTextEffect(ValidatorEffect):
    """A Errortext effect, that will set a text.

    .. versionadded:: 2.2
    """

    effect = ValidatorEffectTypes.ERRORTEXT_EFFECT

    def __init__(self, json=None, text="The validation resulted in an error.", **kwargs):
        """Construct an errortext effect.

        :param json: (optional) dict (json) object to construct the object from
        :type json: dict
        :param text: (optional) text to provide, default empty
        :type text: basestring
        :param kwargs: (optional) additional kwargs to pass down
        :type kwargs: dict
        """
        super(ErrorTextEffect, self).__init__(json=json, **kwargs)


class HelpTextEffect(ValidatorEffect):
    """A Errortext effect, that will set a text.

    .. versionadded:: 2.2
    """

    effect = ValidatorEffectTypes.HELPTEXT_EFFECT

    def __init__(self, json=None, text="", **kwargs):
        """Construct an helptext effect.

        :param json: (optional) dict (json) object to construct the object from
        :type json: dict
        :param text: (optional) text to provide, default empty
        :type text: basestring
        :param kwargs: (optional) additional kwargs to pass down
        :type kwargs: dict
        """
        super(HelpTextEffect, self).__init__(json=json, text=text, **kwargs)


class VisualEffect(ValidatorEffect):
    """A visualeffect, to be processed by the frontend.

    .. versionadded:: 2.2

    :ivar applyCss: css class to apply in case of this effect
    """

    effect = ValidatorEffectTypes.VISUALEFFECT

    def __init__(self, json=None, applyCss=None, **kwargs):
        """Construct an visual effect.

        :param json: (optional) dict (json) object to construct the object from
        :type json: dict
        :param applyCss: (optional) class to apply, defaults to 'valid'
        :type applyCss: basestring
        :param kwargs: (optional) additional kwargs to pass down
        :type kwargs: dict
        """
        super(VisualEffect, self).__init__(json=json, **kwargs)
        self.applyCss = applyCss or self._config.get('applyCss')

    def as_json(self):
        # type: () -> dict
        """Represent effect as JSON dict."""
        self._config['applyCss'] = self.applyCss
        self._json['config'] = self._config
        return self._json


class ValidVisualEffect(VisualEffect):
    """Effect that may apply a css class when the result of the validator is valid.

    .. versionadded:: 2.2
    """

    def __init__(self, json=None, applyCss='valid', **kwargs):
        """Construct an valid visual effect.

        :param json: (optional) dict (json) object to construct the object from
        :type json: dict
        :param applyCss: (optional) class to apply, defaults to 'valid'
        :type applyCss: basestring
        """
        super(ValidVisualEffect, self).__init__(json=json, applyCss=applyCss, **kwargs)


class InvalidVisualEffect(VisualEffect):
    """Effect that may apply a css class when the result of the validator is invalid.

    .. versionadded:: 2.2
    """

    def __init__(self, json=None, applyCss='invalid', **kwargs):
        """Construct an invalid visual effect.

        :param json: (optional) dict (json) object to construct the object from
        :type json: dict
        :param applyCss: (optional) class to apply, defaults to 'invalid'
        :type applyCss: basestring
        """
        super(InvalidVisualEffect, self).__init__(json=json, applyCss=applyCss, **kwargs)
