# -*- coding: utf-8 -*-
# Copyright 2016 LasLabs Inc.
# Copyright 2016 SYLEAM
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from odoo.tests.common import TransactionCase


class TestIrActionsReportXml(TransactionCase):

    def setUp(self):
        super(TestIrActionsReportXml, self).setUp()
        self.Model = self.env['ir.actions.report.xml']
        self.vals = {}

        self.report = self.env['ir.actions.report.xml'].search([], limit=1)
        self.server = self.env['printing.server'].create({})

    def new_action(self):
        return self.env['printing.action'].create({
            'name': 'Printing Action',
            'action_type': 'server',
        })

    def new_printing_action(self):
        return self.env['printing.report.xml.action'].create({
            'report_id': self.report.id,
            'user_id': self.env.ref('base.user_demo').id,
            'action': 'server',
        })

    def new_printer(self):
        return self.env['printing.printer'].create({
            'name': 'Printer',
            'server_id': self.server.id,
            'system_name': 'Sys Name',
            'default': True,
            'status': 'unknown',
            'status_message': 'Msg',
            'model': 'res.users',
            'location': 'Location',
            'uri': 'URI',
        })

    def test_print_action_for_report_name_gets_report(self):
        """ It should get report by name """
        with mock.patch.object(self.Model, 'env') as mk:
            expect = 'test'
            self.Model.print_action_for_report_name(expect)
            mk['report']._get_report_from_name.assert_called_once_with(
                expect
            )

    def test_print_action_for_report_name_returns_if_no_report(self):
        """ It should return empty dict when no matching report """
        with mock.patch.object(self.Model, 'env') as mk:
            expect = 'test'
            mk['report']._get_report_from_name.return_value = False
            res = self.Model.print_action_for_report_name(expect)
            self.assertDictEqual(
                {}, res,
            )

    def test_print_action_for_report_name_returns_if_report(self):
        """ It should return correct serializable result for behaviour """
        with mock.patch.object(self.Model, 'env') as mk:
            res = self.Model.print_action_for_report_name('test')
            behaviour = mk['report']._get_report_from_name().behaviour()[
                mk['report']._get_report_from_name().id
            ]
            expect = {
                'action': behaviour['action'],
                'printer_name': behaviour['printer'].name,
            }
            self.assertDictEqual(
                expect, res,
                'Expect %s, Got %s' % (expect, res),
            )

    def test_behaviour_single_record(self):
        """
        It should return the right action and printer
        Value depends on the report and user settings
        """
        report = self.Model.search([], limit=1)

        # Default values
        self.env.user.printing_action = False
        self.env.user.printing_printer_id = False
        report.property_printing_action_id = False
        report.printing_printer_id = False
        self.assertEqual(report.behaviour(), {
            report.id: {
                'action': 'client',
                'printer': self.env['printing.printer'],
            },
        })

        # User values
        self.env.user.printing_action = 'client'
        self.env.user.printing_printer_id = self.new_printer()
        self.assertEqual(report.behaviour(), {
            report.id: {
                'action': 'client',
                'printer': self.env.user.printing_printer_id,
            },
        })

        # Report values
        report.property_printing_action_id = self.new_action()
        report.printing_printer_id = self.new_printer()
        self.assertEqual(report.behaviour(), {
            report.id: {
                'action': report.property_printing_action_id.action_type,
                'printer': report.printing_printer_id,
            },
        })

        # User action on report
        report.property_printing_action_id.action_type = 'user_default'
        self.assertEqual(report.behaviour(), {
            report.id: {
                'action': 'client',
                'printer': report.printing_printer_id,
            },
        })

        # Printing action on the wrong user
        printing_action = self.new_printing_action()
        printing_action.user_id = self.env['res.users'].search([
            ('id', '!=', self.env.user.id),
        ], limit=1)
        self.assertEqual(report.behaviour(), {
            report.id: {
                'action': 'client',
                'printer': report.printing_printer_id,
            },
        })

        # Printing action on the wrong report
        printing_action.user_id = self.env.user
        printing_action.report_id = self.env['ir.actions.report.xml'].search([
            ('id', '!=', report.id),
        ], limit=1)
        self.assertEqual(report.behaviour(), {
            report.id: {
                'action': 'client',
                'printer': report.printing_printer_id,
            },
        })

        # Printing action with no printer
        printing_action.report_id = report
        self.assertEqual(report.behaviour(), {
            report.id: {
                'action': printing_action.action,
                'printer': report.printing_printer_id,
            },
        })

        # Printing action with printer
        printing_action.printer_id = self.new_printer()
        self.assertEqual(report.behaviour(), {
            report.id: {
                'action': printing_action.action,
                'printer': printing_action.printer_id,
            },
        })

        # Printing action defining user defaults
        printing_action.action = 'user_default'
        self.assertEqual(report.behaviour(), {
            report.id: {
                'action': 'client',
                'printer': report.printing_printer_id,
            },
        })
