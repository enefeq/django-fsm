from django.db import models
from django.test import TestCase

from django_fsm import FSMField, transition, GET_STATE, RETURN_VALUE
from django_fsm.signals import pre_transition, post_transition


class BlogPostWithStateTransitions(models.Model):
    state = FSMField(default='new')

    @transition(field=state, source='new', target=RETURN_VALUE('for_moderators', 'published'))
    def publish(self, is_public=False):
        return 'need_moderation' if is_public else 'published'

    @transition(
        field=state,
        source='for_moderators',
        target=GET_STATE(
            lambda self, allowed: 'published' if allowed else 'rejected',
            states=['published', 'rejected']))
    def moderate(self, allowed):
        self.allowed = allowed


class TestSignalsWithStateObjects(TestCase):
    def setUp(self):
        self.model = BlogPostWithStateTransitions()
        self.pre_transition_called = False
        self.post_transition_called = False
        pre_transition.connect(self.on_pre_transition, sender=BlogPostWithStateTransitions)
        post_transition.connect(self.on_post_transition, sender=BlogPostWithStateTransitions)

    def on_pre_transition(self, sender, instance, name, source, target, **kwargs):
        self.assertEqual(instance.state, source)
        self.pre_transition_called = True

    def on_post_transition(self, sender, instance, name, source, target, **kwargs):
        self.assertEqual(instance.state, target)
        self.post_transition_called = True

    def test_signals_called_with_get_state(self):
        self.model.moderate(allowed=True)
        self.assertTrue(self.pre_transition_called)
        self.assertTrue(self.post_transition_called)

    def test_signals_called_with_return_value(self):
        self.model.publish()
        self.assertTrue(self.pre_transition_called)
        self.assertTrue(self.post_transition_called)
