"""Tests for vizier.service.service_policy_supporter."""
from vizier.pyvizier import oss
from vizier.service import resources
from vizier.service import service_policy_supporter
from vizier.service import study_pb2
from vizier.service import test_util
from vizier.service import vizier_server

from absl.testing import absltest


class PythiaSupporterTest(absltest.TestCase):

  def setUp(self):
    self.owner_id = 'my_username'
    self.study_id = '1231223'
    self.study_name = resources.StudyResource(
        owner_id=self.owner_id, study_id=self.study_id).name
    self.vs = vizier_server.VizierService()
    self.example_study = test_util.generate_study(self.owner_id, self.study_id)
    self.vs.datastore.create_study(self.example_study)

    self.basic_example_trials = test_util.generate_trials(
        range(1, 6), self.owner_id, self.study_id)

    self.active_trial = test_util.generate_trials(
        [6], self.owner_id, self.study_id,
        state=study_pb2.Trial.State.ACTIVE)[0]

    self.succeeded_trial = test_util.generate_trials(
        [7],
        self.owner_id,
        self.study_id,
        state=study_pb2.Trial.State.SUCCEEDED)[0]

    for trial in self.basic_example_trials + [
        self.active_trial, self.succeeded_trial
    ]:
      self.vs.datastore.create_trial(trial)

    self.policy_supporter = service_policy_supporter.ServicePolicySupporter(
        self.vs)

    super().setUp()

  def test_trial_names_filter(self):
    suggest_decisions = self.policy_supporter.GetTrials(
        study_guid=self.study_name, trial_ids=[3, 4])

    self.assertEqual(
        suggest_decisions[0].parameters,
        oss.TrialConverter.from_proto(self.basic_example_trials[2]).parameters)
    self.assertEqual(
        suggest_decisions[1].parameters,
        oss.TrialConverter.from_proto(self.basic_example_trials[3]).parameters)

  def test_min_max_filter(self):
    suggest_decisions = self.policy_supporter.GetTrials(
        study_guid=self.study_name, min_trial_id=3, max_trial_id=4)

    self.assertEqual(
        suggest_decisions[0].parameters,
        oss.TrialConverter.from_proto(self.basic_example_trials[2]).parameters)
    self.assertEqual(
        suggest_decisions[1].parameters,
        oss.TrialConverter.from_proto(self.basic_example_trials[3]).parameters)

  def test_status_match_filter(self):
    suggest_decisions = self.policy_supporter.GetTrials(
        study_guid=self.study_name, status_matches=study_pb2.Trial.State.ACTIVE)

    self.assertLen(suggest_decisions, 1)
    self.assertEqual(
        suggest_decisions[0].parameters,
        oss.TrialConverter.from_proto(self.active_trial).parameters)

  def test_raise_value_error(self):

    def should_raise_value_error_fn():
      self.policy_supporter.GetTrials(
          study_guid=self.study_name,
          trial_ids=[1],
          status_matches=study_pb2.Trial.State.ACTIVE)

      with self.assertRaises(ValueError):
        should_raise_value_error_fn()

  def test_get_study_config(self):
    pythia_sc = self.policy_supporter.GetStudyConfig(self.study_name)
    correct_pythia_sc = oss.StudyConfig.from_proto(
        self.example_study.study_spec).to_pythia()
    self.assertEqual(pythia_sc, correct_pythia_sc)


if __name__ == '__main__':
  absltest.main()