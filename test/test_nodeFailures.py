#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ####################################################################
# Copyright (C) 2016  Fridolin Pokorny, fpokorny@redhat.com
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
# ####################################################################

import pytest
from selinonTestCase import SelinonTestCase

from selinon import FlowError
from selinon import SystemState


class TestNodeFailures(SelinonTestCase):
    def test_single_failure_flow_fail(self):
        #
        # flow1:
        #
        #     Task1 X
        #       |
        #       |
        #     Task2
        #
        # Note:
        #   Task1 will fail
        #
        edge_table = {
            'flow1': [{'from': ['Task1'], 'to': ['Task2'], 'condition': self.cond_true},
                      {'from': [], 'to': ['Task1'], 'condition': self.cond_true}]
        }
        failures = {
            'flow1': {'Task1': {'next:': {}, 'fallback': []}}
        }
        self.init(edge_table, failures=failures)

        system_state = SystemState(id(self), 'flow1')
        retry = system_state.update()
        state_dict = system_state.to_dict()

        assert retry is not None
        assert system_state.node_args is None
        assert 'Task1' in self.instantiated_tasks
        assert 'Task2' not in self.instantiated_tasks
        assert len(state_dict.get('waiting_edges')) == 1
        assert state_dict['waiting_edges'][0] == 0

        # Task1 has failed
        task1 = self.get_task('Task1')
        self.set_failed(task1, KeyError("Some exception raised"))

        with pytest.raises(FlowError):
            system_state = SystemState(id(self), 'flow1', state=state_dict,
                                       node_args=system_state.node_args)
            system_state.update()

        assert 'Task2' not in self.instantiated_tasks

    def test_single_failure_flow_fallback_true(self):
        #
        # flow1:
        #
        #     Task1 X .... True
        #       |
        #       |
        #     Task2
        #
        # Note:
        #   Task1 will fail
        #
        edge_table = {
            'flow1': [{'from': ['Task1'], 'to': ['Task2'], 'condition': self.cond_true},
                      {'from': [], 'to': ['Task1'], 'condition': self.cond_true}]
        }
        failures = {
            'flow1': {'Task1': {'next:': {}, 'fallback': True}}

        }
        self.init(edge_table, failures=failures)

        system_state = SystemState(id(self), 'flow1')
        retry = system_state.update()
        state_dict = system_state.to_dict()

        assert retry is not None
        assert system_state.node_args is None
        assert 'Task1' in self.instantiated_tasks
        assert 'Task2' not in self.instantiated_tasks
        assert len(state_dict.get('waiting_edges')) == 1
        assert state_dict['waiting_edges'][0] == 0

        # Task1 has failed
        task1 = self.get_task('Task1')
        self.set_failed(task1, KeyError("Some exception raised"))

        system_state = SystemState(id(self), 'flow1', state=state_dict,
                                   node_args=system_state.node_args)
        retry = system_state.update()
        state_dict = system_state.to_dict()

        assert retry is None
        assert system_state.node_args is None
        assert 'Task1' in self.instantiated_tasks
        assert 'Task2' not in self.instantiated_tasks
        assert len(state_dict.get('waiting_edges')) == 1
        assert state_dict['waiting_edges'][0] == 0

    def test_single_failure_flow_fallback_start(self):
        #
        # flow1:
        #
        #     Task1 X .... Task3
        #       |            |
        #       |            |
        #     Task2        Task4
        #
        # Note:
        #   Task1 will fail
        #
        edge_table = {
            'flow1': [{'from': ['Task1'], 'to': ['Task2'], 'condition': self.cond_true},
                      {'from': [], 'to': ['Task1'], 'condition': self.cond_true},
                      {'from': ['Task3'], 'to': ['Task4'], 'condition': self.cond_true}]
        }
        failures = {
            'flow1': {'Task1': {'next:': {}, 'fallback': ['Task3']}}

        }
        self.init(edge_table, failures=failures)

        node_args = {'foo': 'bar'}
        system_state = SystemState(id(self), 'flow1', node_args=node_args)
        retry = system_state.update()
        state_dict = system_state.to_dict()

        assert retry is not None
        assert system_state.node_args == node_args
        assert 'Task1' in self.instantiated_tasks
        assert 'Task2' not in self.instantiated_tasks
        assert len(state_dict.get('waiting_edges')) == 1
        assert state_dict['waiting_edges'][0] == 0

        # Task1 has failed
        task1 = self.get_task('Task1')
        self.set_failed(task1)

        system_state = SystemState(id(self), 'flow1', state=state_dict,
                                   node_args=system_state.node_args)
        retry = system_state.update()
        state_dict = system_state.to_dict()

        assert retry is not None
        assert system_state.node_args == node_args
        assert 'Task1' in self.instantiated_tasks
        assert 'Task3' in self.instantiated_tasks
        assert 'Task2' not in self.instantiated_tasks
        assert len(state_dict.get('waiting_edges')) == 1
        assert state_dict['waiting_edges'][0] == 0

        task3 = self.get_task('Task3')
        assert task3.node_args == node_args

    def test_single_failure_flow_fallback_start2(self):
        #
        # flow1:
        #
        #     Task1 X .... Task3, Task4
        #       |
        #       |
        #     Task2
        #
        #     Task3      Task4
        #       |          |
        #       |          |
        #     Task5      Task6
        #
        # Note:
        #   Task1 will fail
        #
        edge_table = {
            'flow1': [{'from': ['Task1'], 'to': ['Task2'], 'condition': self.cond_true},
                      {'from': [], 'to': ['Task1'], 'condition': self.cond_true},
                      {'from': ['Task3'], 'to': ['Task5'], 'condition': self.cond_true},
                      {'from': ['Task4'], 'to': ['Task6'], 'condition': self.cond_true}]
        }
        failures = {
            'flow1': {'Task1': {'next:': {}, 'fallback': ['Task3', 'Task4']}}

        }
        self.init(edge_table, failures=failures)

        node_args = {'foo': 'bar'}
        system_state = SystemState(id(self), 'flow1', node_args=node_args)
        retry = system_state.update()
        state_dict = system_state.to_dict()

        assert retry is not None
        assert system_state.node_args == node_args
        assert 'Task1' in self.instantiated_tasks
        assert 'Task2' not in self.instantiated_tasks
        assert len(state_dict.get('waiting_edges')) == 1
        assert state_dict['waiting_edges'][0] == 0

        # Task1 has failed
        task1 = self.get_task('Task1')
        self.set_failed(task1, KeyError("Some exception raised"))

        system_state = SystemState(id(self), 'flow1', state=state_dict,
                                   node_args=system_state.node_args)
        retry = system_state.update()
        state_dict = system_state.to_dict()

        assert retry is not None
        assert system_state.node_args == node_args
        assert 'Task1' in self.instantiated_tasks
        assert 'Task3' in self.instantiated_tasks
        assert 'Task4' in self.instantiated_tasks
        assert 'Task2' not in self.instantiated_tasks
        assert len(state_dict.get('waiting_edges')) == 1
        assert state_dict['waiting_edges'][0] == 0

        task3 = self.get_task('Task3')
        task4 = self.get_task('Task4')

        assert task3.node_args == node_args
        assert task4.node_args == node_args

        # Now let's finish Task3 and Task4 to see that they correctly continue
        self.set_finished(task3)
        self.set_finished(task4)

        system_state = SystemState(id(self), 'flow1', state=state_dict,
                                   node_args=system_state.node_args)
        retry = system_state.update()
        state_dict = system_state.to_dict()

        assert retry is not None
        assert system_state.node_args == node_args
        assert 'Task1' in self.instantiated_tasks
        assert 'Task3' in self.instantiated_tasks
        assert 'Task4' in self.instantiated_tasks
        assert 'Task5' in self.instantiated_tasks
        assert 'Task6' in self.instantiated_tasks
        assert 'Task2' not in self.instantiated_tasks
        assert len(state_dict.get('waiting_edges')) == 3
        assert state_dict['waiting_edges'][0] == 0
        assert 2 in state_dict['waiting_edges']
        assert 3 in state_dict['waiting_edges']
        assert 'Task3' in state_dict['finished_nodes']
        assert 'Task4' in state_dict['finished_nodes']

        # Finish the flow!
        task5 = self.get_task('Task5')
        task6 = self.get_task('Task6')

        self.set_finished(task5)
        self.set_finished(task6)

        system_state = SystemState(id(self), 'flow1', state=state_dict,
                                   node_args=system_state.node_args)
        retry = system_state.update()
        assert retry is None

    def test_single_failure_flow_fallback_to_flow(self):
        #
        # flow1:
        #
        #     Task1 X .... flow2
        #       |
        #       |
        #     Task2
        #
        # Note:
        #   Task1 will fail
        #
        edge_table = {
            'flow1': [{'from': ['Task1'], 'to': ['Task2'], 'condition': self.cond_true},
                      {'from': [], 'to': ['Task1'], 'condition': self.cond_true}],
            'flow2': [{'from': [], 'to': ['Task3'], 'condition': self.cond_true}]
        }
        failures = {
            'flow1': {'Task1': {'next:': {}, 'fallback': ['flow2']}}
        }
        self.init(edge_table, failures=failures)

        node_args = {'foo': 'bar'}
        system_state = SystemState(id(self), 'flow1', node_args=node_args)
        retry = system_state.update()
        state_dict = system_state.to_dict()

        assert retry is not None
        assert system_state.node_args == node_args
        assert 'Task1' in self.instantiated_tasks
        assert 'flow2' not in self.instantiated_flows
        assert len(state_dict.get('waiting_edges')) == 1
        assert state_dict['waiting_edges'][0] == 0

        # Task1 has failed
        task1 = self.get_task('Task1')
        self.set_failed(task1, KeyError("Some exception raised"))

        system_state = SystemState(id(self), 'flow1', state=state_dict,
                                   node_args=system_state.node_args)
        retry = system_state.update()
        state_dict = system_state.to_dict()

        assert retry is not None
        assert system_state.node_args == node_args
        assert 'Task1' in self.instantiated_tasks
        assert 'flow2' in self.instantiated_flows
        assert 'Task2' not in self.instantiated_tasks
        assert len(state_dict.get('waiting_edges')) == 1
        assert state_dict['waiting_edges'][0] == 0

    def test_singe_failure_flow_fallback(self):
        #
        # flow1:
        #
        #     flow2 X ... Task2
        #       |
        #       |
        #     Task1
        #
        # Note:
        #   flow2 will fail
        #
        edge_table = {
            'flow1': [{'from': ['flow2'], 'to': ['Task1'], 'condition': self.cond_true},
                      {'from': [], 'to': ['flow2'], 'condition': self.cond_true}],
            'flow2': []
        }
        failures = {
            'flow1': {'flow2': {'next:': {}, 'fallback': ['Task2']}}
        }
        self.init(edge_table, failures=failures)

        system_state = SystemState(id(self), 'flow1')
        retry = system_state.update()
        state_dict = system_state.to_dict()

        assert retry is not None
        assert system_state.node_args is None
        assert 'flow2' in self.instantiated_flows
        assert 'Task1' not in self.instantiated_tasks
        assert len(state_dict.get('waiting_edges')) == 1
        assert state_dict['waiting_edges'][0] == 0

        # flow2 has failed
        flow2 = self.get_flow('flow2')
        flow_info = {'finished_nodes': {'Task1': ['id_task1']}, 'failed_nodes': {'Task2': ['id_task21']}}
        self.set_failed(flow2, FlowError(flow_info))

        system_state = SystemState(id(self), 'flow1', state=state_dict, node_args=system_state.node_args)
        retry = system_state.update()
        state_dict = system_state.to_dict()

        assert retry is not None
        assert system_state.node_args is None
        assert 'flow2' in self.instantiated_flows
        assert 'Task2' in self.instantiated_tasks
        assert len(state_dict.get('waiting_edges')) == 1
        assert state_dict['waiting_edges'][0] == 0

    def test_two_failures_no_fallback(self):
        #
        # flow1:
        #
        #    Task1 X     Task2 X
        #       |           |
        #       |           |
        #    Task3        Task4
        #
        # Note:
        #   Task1 will fail, then Task2 will fail
        #
        edge_table = {
            'flow1': [{'from': ['Task1'], 'to': ['Task3'], 'condition': self.cond_true},
                      {'from': ['Task2'], 'to': ['Task4'], 'condition': self.cond_true},
                      {'from': [], 'to': ['Task1', 'Task2'], 'condition': self.cond_true}],
        }
        failures = {
            'flow1': {'Task1': {'next': {'Task2': {'next': {}, 'fallback': []}}, 'fallback': []},
                      'Task2': {'next': {'Task1': {'next': {}, 'fallback': []}}, 'fallback': []}
                     }
        }
        self.init(edge_table, failures=failures)

        system_state = SystemState(id(self), 'flow1')
        retry = system_state.update()
        state_dict = system_state.to_dict()

        assert retry is not None
        assert system_state.node_args is None
        assert 'Task1' in self.instantiated_tasks
        assert 'Task2' in self.instantiated_tasks
        assert 'Task3' not in self.instantiated_tasks
        assert 'Task4' not in self.instantiated_tasks
        assert 'Task5' not in self.instantiated_tasks
        assert len(state_dict.get('waiting_edges')) == 2
        assert 0 in state_dict['waiting_edges']
        assert 1 in state_dict['waiting_edges']

        task1 = self.get_task('Task1')
        self.set_failed(task1)

        system_state = SystemState(id(self), 'flow1', state=state_dict,
                                   node_args=system_state.node_args)
        retry = system_state.update()
        state_dict = system_state.to_dict()

        assert retry is not None
        assert system_state.node_args is None
        assert 'Task1' in self.instantiated_tasks
        assert 'Task2' in self.instantiated_tasks
        assert 'Task3' not in self.instantiated_tasks
        assert 'Task4' not in self.instantiated_tasks
        assert 'Task5' not in self.instantiated_tasks
        assert len(state_dict.get('waiting_edges')) == 2
        assert 0 in state_dict['waiting_edges']
        assert 1 in state_dict['waiting_edges']
        assert 'Task1' in state_dict['failed_nodes']

        # No change so far
        system_state = SystemState(id(self), 'flow1', state=state_dict,
                                   node_args=system_state.node_args)
        retry = system_state.update()
        state_dict = system_state.to_dict()

        assert retry is not None
        assert system_state.node_args is None
        assert 'Task1' in self.instantiated_tasks
        assert 'Task2' in self.instantiated_tasks
        assert 'Task3' not in self.instantiated_tasks
        assert 'Task4' not in self.instantiated_tasks
        assert 'Task5' not in self.instantiated_tasks
        assert len(state_dict.get('waiting_edges')) == 2
        assert 0 in state_dict['waiting_edges']
        assert 1 in state_dict['waiting_edges']
        assert 'Task1' in state_dict['failed_nodes']

        # Task2 has failed
        task2 = self.get_task('Task2')
        self.set_failed(task2)

        with pytest.raises(FlowError):
            system_state = SystemState(id(self), 'flow1', state=state_dict,
                                       node_args=system_state.node_args)
            system_state.update()

    def test_two_failures_fallback_start(self):
        #
        # flow1:
        #
        #    Task1 X     Task2 X
        #       |           |
        #       |           |
        #    Task3        Task4
        #
        # Note:
        #   Task1 will fail, then Task2 will fail; fallback for Task1, Task2 is Task5
        #
        edge_table = {
            'flow1': [{'from': ['Task1'], 'to': ['Task3'], 'condition': self.cond_true},
                      {'from': ['Task2'], 'to': ['Task4'], 'condition': self.cond_true},
                      {'from': [], 'to': ['Task1', 'Task2'], 'condition': self.cond_true}],
        }
        failures = {
            'flow1': {'Task1': {'next': {'Task2': {'next': {}, 'fallback': ['Task5']}}, 'fallback': []},
                      'Task2': {'next': {'Task1': {'next': {}, 'fallback': ['Task5']}}, 'fallback': []}
                      }
        }
        self.init(edge_table, failures=failures)

        system_state = SystemState(id(self), 'flow1')
        retry = system_state.update()
        state_dict = system_state.to_dict()

        assert retry is not None
        assert system_state.node_args is None
        assert 'Task1' in self.instantiated_tasks
        assert 'Task2' in self.instantiated_tasks
        assert 'Task3' not in self.instantiated_tasks
        assert 'Task4' not in self.instantiated_tasks
        assert 'Task5' not in self.instantiated_tasks
        assert len(state_dict.get('waiting_edges')) == 2
        assert 0 in state_dict['waiting_edges']
        assert 1 in state_dict['waiting_edges']

        task1 = self.get_task('Task1')
        self.set_failed(task1, KeyError("Some exception raised"))

        system_state = SystemState(id(self), 'flow1', state=state_dict,
                                   node_args=system_state.node_args)
        retry = system_state.update()
        state_dict = system_state.to_dict()

        assert retry is not None
        assert system_state.node_args is None
        assert 'Task1' in self.instantiated_tasks
        assert 'Task2' in self.instantiated_tasks
        assert 'Task3' not in self.instantiated_tasks
        assert 'Task4' not in self.instantiated_tasks
        assert 'Task5' not in self.instantiated_tasks
        assert len(state_dict.get('waiting_edges')) == 2
        assert 0 in state_dict['waiting_edges']
        assert 1 in state_dict['waiting_edges']
        assert 'Task1' in state_dict['failed_nodes']

        # Task2 has failed
        task2 = self.get_task('Task2')
        self.set_failed(task2)

        system_state = SystemState(id(self), 'flow1', state=state_dict,
                                   node_args=system_state.node_args)
        system_state.update()
        state_dict = system_state.to_dict()

        assert retry is not None
        assert system_state.node_args is None
        assert 'Task1' in self.instantiated_tasks
        assert 'Task2' in self.instantiated_tasks
        assert 'Task3' not in self.instantiated_tasks
        assert 'Task4' not in self.instantiated_tasks
        assert 'Task5' in self.instantiated_tasks
        assert len(state_dict.get('waiting_edges')) == 2
        assert 0 in state_dict['waiting_edges']
        assert 1 in state_dict['waiting_edges']
        assert 'Task1' not in state_dict['failed_nodes']
        assert 'Task2' not in state_dict['failed_nodes']

    def test_single_failure_finish_wait(self):
        #
        # flow1:
        #
        #    Task1       Task2 X
        #       |           |
        #       |           |
        #    Task3        Task4
        #
        # No fallback defined for Task2
        #
        # Note:
        #   Task2 will fail, no fallback defined, Dispatcher should wait for Task1 to finish and
        #   raise FlowError exception
        edge_table = {
            'flow1': [{'from': ['Task1'], 'to': ['Task3'], 'condition': self.cond_true},
                      {'from': ['Task2'], 'to': ['Task4'], 'condition': self.cond_true},
                      {'from': [], 'to': ['Task1', 'Task2'], 'condition': self.cond_true}],
        }
        failures = {
            'flow1': {'Task1': {'next': {'Task2': {'next': {}, 'fallback': []}}, 'fallback': []},
                      'Task2': {'next': {'Task1': {'next': {}, 'fallback': []}}, 'fallback': []}
                      }
        }
        self.init(edge_table, failures=failures)

        system_state = SystemState(id(self), 'flow1')
        retry = system_state.update()
        state_dict = system_state.to_dict()

        assert retry is not None
        assert system_state.node_args is None
        assert 'Task1' in self.instantiated_tasks
        assert 'Task2' in self.instantiated_tasks
        assert 'Task3' not in self.instantiated_tasks
        assert 'Task4' not in self.instantiated_tasks
        assert 'Task5' not in self.instantiated_tasks
        assert len(state_dict.get('waiting_edges')) == 2
        assert 0 in state_dict['waiting_edges']
        assert 1 in state_dict['waiting_edges']

        # Task2 has failed
        task2 = self.get_task('Task2')
        self.set_failed(task2)

        system_state = SystemState(id(self), 'flow1', state=state_dict,
                                   node_args=system_state.node_args)
        system_state.update()
        state_dict = system_state.to_dict()

        assert retry is not None
        assert system_state.node_args is None
        assert 'Task1' in self.instantiated_tasks
        assert 'Task2' in self.instantiated_tasks
        assert 'Task3' not in self.instantiated_tasks
        assert 'Task4' not in self.instantiated_tasks
        assert 'Task5' not in self.instantiated_tasks
        assert len(state_dict.get('waiting_edges')) == 2
        assert 0 in state_dict['waiting_edges']
        assert 1 in state_dict['waiting_edges']
        assert 'Task2' in state_dict['failed_nodes']

        # No change so far, still wait
        system_state = SystemState(id(self), 'flow1', state=state_dict,
                                   node_args=system_state.node_args)
        system_state.update()
        state_dict = system_state.to_dict()

        assert retry is not None
        assert system_state.node_args is None
        assert 'Task1' in self.instantiated_tasks
        assert 'Task2' in self.instantiated_tasks
        assert 'Task3' not in self.instantiated_tasks
        assert 'Task4' not in self.instantiated_tasks
        assert 'Task5' not in self.instantiated_tasks
        assert len(state_dict.get('waiting_edges')) == 2
        assert 0 in state_dict['waiting_edges']
        assert 1 in state_dict['waiting_edges']
        assert 'Task2' in state_dict['failed_nodes']

        # Task1 has finished successfully
        task1 = self.get_task('Task1')
        self.set_finished(task1, 0)

        # Wait for Task3
        system_state = SystemState(id(self), 'flow1', state=state_dict,
                                   node_args=system_state.node_args)
        system_state.update()
        state_dict = system_state.to_dict()

        assert retry is not None
        assert 'Task3' in self.instantiated_tasks
        assert 'Task4' not in self.instantiated_tasks

        # Task3 has finished successfully
        task3 = self.get_task('Task3')
        self.set_finished(task3, 0)

        with pytest.raises(FlowError):
            system_state = SystemState(id(self), 'flow1', state=state_dict,
                                       node_args=system_state.node_args)
            system_state.update()

    def test_flow_failure(self):
        #
        # flow1:
        #
        #    flow2 X      flow4 X    Task1_f1    Task2_f1 X   flow5
        #       |           |           |         |             |
        #        ................................................
        #                             |
        #                           TaskX
        #
        # flow2:
        #
        #     Task1_f2    Task2_f2 X   Task3_f2   flow3
        #
        # flow3:
        #
        #     Task1_f3    Task2_f3 X   Task3_f3 X
        #
        # flow4:
        #
        #     Task1_f4    Task2_f4 X   Task3_f4
        #
        # flow5:
        #     Task1_f5    Task2_f5 X
        #
        # Note:
        #  All flows fail, we inspect finished propagation in flow1 in case of failure. Tasks marked with X will fail.
        #
        edge_table = {
            'flow1': [{'from': ['flow2', 'flow5', 'flow4', 'Task1_f1', 'Task2_f1'], 'to': ['TaskX'], 'condition': self.cond_true},
                      {'from': [], 'to': ['Task1_f1', 'Task2_f1', 'flow2', 'flow4', 'flow5'], 'condition': self.cond_true}],
            'flow2': [{'from': [], 'to': ['Task1_f2', 'Task2_f2', 'Task3_f2', 'flow3'], 'condition': self.cond_true}],
            'flow3': [{'from': [], 'to': ['Task1_f3', 'Task2_f3', 'Task3_f3'], 'condition': self.cond_true}],
            'flow4': [{'from': [], 'to': ['Task1_f4', 'Task2_f4', 'Task3_f4'], 'condition': self.cond_true}],
            'flow5': [{'from': [], 'to': ['Task1_f5', 'Task2_f5'], 'condition': self.cond_true}]
        }
        failures = {
            'flow1': {
                'Task2_f1': {
                    'next': {
                        'flow2': {
                            'next': {
                                'flow4': {
                                    'next': {},
                                    'fallback': ['TaskX']
                                },
                                'fallback': []
                            },
                            'fallback': []
                        },
                        'fallback': []
                    },
                    'fallback': []
                },
                'fallback': []
            },
            'fallback': []
        }
        self.init(edge_table, failures=failures, propagate_parent=dict.fromkeys(edge_table, True))

        system_state = SystemState(id(self), 'flow1')
        retry = system_state.update()
        state_dict_1 = system_state.to_dict()

        assert retry is not None
        assert system_state.node_args is None
        assert 'flow2' in self.instantiated_flows
        assert 'flow4' in self.instantiated_flows
        assert 'flow5' in self.instantiated_flows
        assert 'Task1_f1' in self.instantiated_tasks
        assert 'Task2_f1' in self.instantiated_tasks
        assert 'flow3' not in self.instantiated_flows

        # Task1_f1 have finished
        task1_f1 = self.get_task('Task1_f1')
        self.set_finished(task1_f1, 0)

        # Task2_f1 has failed
        task2_f1 = self.get_task('Task2_f1')
        self.set_failed(task2_f1)

        system_state = SystemState(id(self), 'flow1', state=state_dict_1, node_args=system_state.node_args)
        retry = system_state.update()
        state_dict_1 = system_state.to_dict()

        assert retry is not None
        assert system_state.node_args is None
        assert 'flow3' not in self.instantiated_flows

        # flow2

        system_state = SystemState(id(self), 'flow2')
        retry = system_state.update()
        state_dict_2 = system_state.to_dict()
        flow2 = self.get_flow('flow2')

        assert retry is not None
        assert system_state.node_args is None
        assert 'Task1_f2' in self.instantiated_tasks
        assert 'Task2_f2' in self.instantiated_tasks
        assert 'Task3_f2' in self.instantiated_tasks
        assert 'flow3' in self.instantiated_flows

        # Task1_f2, Task3_f2 have finished
        task1_f2 = self.get_task('Task1_f2')
        self.set_finished(task1_f2, 1)

        task3_f2 = self.get_task('Task3_f2')
        self.set_finished(task3_f2, 2)

        # Task2_f2 has failed
        task2_f2 = self.get_task('Task2_f2')
        self.set_failed(task2_f2)

        system_state = SystemState(id(self), 'flow2', state=state_dict_2, node_args=system_state.node_args)
        retry = system_state.update()
        state_dict_2 = system_state.to_dict()

        assert retry is not None
        assert system_state.node_args is None

        # flow 3

        system_state = SystemState(id(self), 'flow3')
        retry = system_state.update()
        state_dict_3 = system_state.to_dict()
        flow3 = self.get_flow('flow3')

        assert retry is not None
        assert system_state.node_args is None
        assert 'Task1_f3' in self.instantiated_tasks
        assert 'Task2_f3' in self.instantiated_tasks
        assert 'Task3_f3' in self.instantiated_tasks

        # Task1_f3 has finished
        task1_f3 = self.get_task('Task1_f3')
        self.set_finished(task1_f3, 3)

        # Task2_f3, Task2_f3 have failed
        task2_f3 = self.get_task('Task2_f3')
        self.set_failed(task2_f3)

        task3_f3 = self.get_task('Task3_f3')
        self.set_failed(task3_f3)

        try:
            system_state = SystemState(id(self), 'flow3', state=state_dict_3, node_args=system_state.node_args)
            system_state.update()
        except FlowError as exc:
            self.set_failed(flow3, exc)
        else:
            assert not "Expected FlowError not raised"

        # flow4

        system_state = SystemState(id(self), 'flow4')
        retry = system_state.update()
        state_dict_4 = system_state.to_dict()
        flow4 = self.get_flow('flow4')

        assert retry is not None
        assert system_state.node_args is None
        assert 'Task1_f4' in self.instantiated_tasks
        assert 'Task2_f4' in self.instantiated_tasks
        assert 'Task3_f4' in self.instantiated_tasks

        # Task1_f2, Task3_f2 have finished
        task1_f4 = self.get_task('Task1_f4')
        self.set_finished(task1_f4, 1)

        task3_f4 = self.get_task('Task3_f4')
        self.set_finished(task3_f4, 4)

        # Task2_f4 has failed
        task2_f4 = self.get_task('Task2_f4')
        self.set_failed(task2_f4)

        try:
            system_state = SystemState(id(self), 'flow4', state=state_dict_4, node_args=system_state.node_args)
            system_state.update()
        except FlowError as exc:
            self.set_failed(flow4, exc)
        else:
            assert not "Expected FlowError not raised"

        # flow5

        system_state = SystemState(id(self), 'flow5')
        retry = system_state.update()
        state_dict_5 = system_state.to_dict()
        flow5 = self.get_flow('flow5')

        assert retry is not None
        assert system_state.node_args is None
        assert 'Task1_f5' in self.instantiated_tasks
        assert 'Task2_f5' in self.instantiated_tasks

        # Task1_f5, Task2_f5 have finished
        task1_f5 = self.get_task('Task1_f5')
        self.set_finished(task1_f5, 1)
        task2_f5 = self.get_task('Task2_f5')
        self.set_finished(task2_f5, 2)

        system_state = SystemState(id(self), 'flow5', state=state_dict_5, node_args=system_state.node_args)
        retry = system_state.update()

        assert retry is None
        state_info = {
            'finished_nodes': system_state.to_dict()['finished_nodes'],
            'failed_nodes': system_state.to_dict()['failed_nodes']
        }
        self.set_finished(flow5, state_info)

        # Back to flow2, all child finished

        try:
            system_state = SystemState(id(self), 'flow2', state=state_dict_2, node_args=system_state.node_args)
            system_state.update()
        except FlowError as exc:
            self.set_failed(flow2, exc)
        else:
            assert not "Expected FlowError not raised"

        # finally inspect flow1 result and finished that is propagated at fallback to TaskX

        assert 'TaskX' not in self.instantiated_tasks

        system_state = SystemState(id(self), 'flow1', state=state_dict_1, node_args=system_state.node_args)
        system_state.update()

        assert 'TaskX' in self.instantiated_tasks

        task_x = self.get_task('TaskX')
        assert task_x.parent is None
