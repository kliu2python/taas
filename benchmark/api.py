from flask import jsonify
from flask_restx import Resource, fields, Namespace
from flask_restful import request

import benchmark.services.reporting as service
from benchmark.tasks.lifecycle import check_job_status
from rest import RestApi

# Initialize RestApi with base_route
rest = RestApi(base_route="/benchmark/v1/")

# Create 'Result' namespace for Result DB operations
ns_result = Namespace('benchmark/v1/', description='Benchmark DB operations')

# Define models under the 'ns_result' namespace
result_model = ns_result.model('Result', {
    'job_name': fields.String(required=True, description='Jenkins job name'),
    'build_id': fields.String(required=True, description='Jenkins build number'),
    'platform': fields.String(required=True, description='DUT Model / Platform'),
    'version': fields.String(required=True, description='FOS Version on DUT'),
    'user': fields.String(required=True, description='Trigger / Test Owner'),
    'test': fields.String(required=True, description='Test Case Name'),
    'settings': fields.String(description='Settings / Comments'),
    'start_time': fields.String(description='Run start time'),
    'end_time': fields.String(description='Run end time'),
})

# Additional models can be defined similarly
counter_model = ns_result.model('Counter', {
    'job_name': fields.String(required=True, description='Jenkins job name'),
    'build_id': fields.String(required=True, description='Jenkins build number'),
    'idx': fields.String(required=True, description='Device/platform/Index'),
    'counter': fields.String(required=True, description='Perf counter (e.g., cpu, memory, bw)'),
    'datetime': fields.String(description='Datetime of the record'),
    'value': fields.String(required=True, description='Value of the counter (TEXT)')
})

log_model = ns_result.model('Log', {
    'job_name': fields.String(required=True, description='Jenkins job name'),
    'build_id': fields.String(required=True, description='Jenkins build number'),
    'platform': fields.String(required=True, description='DUT Model / Platform'),
    'version': fields.String(required=True, description='FOS Version on DUT'),
    'timestamp': fields.String(description='Optional timestamp'),
    'test': fields.String(description='Test case name (optional)'),
    'log': fields.String(required=True, description='Log content')
})

# Register the namespace with 'rest'
rest.add_namespace(ns_result)


# Define Result API endpoint under the 'ns_result' namespace
@ns_result.route("/result/<string:job_name>/<string:build_id>")
class ResultAll(Resource):
    @ns_result.doc('get_result', params={
        'job_name': 'Jenkins job name',
        'build_id': 'Jenkins build number'}
                   )
    def get(self, job_name, build_id):
        """Get result by job_name and build_id"""
        msg = service.ResultApi.read_all(job_name=job_name, build_id=build_id)
        return jsonify(msg)


@ns_result.route("/result/<string:job_name>/<string:build_id>/<string"
                 ":case_name>")
class ResultOne(Resource):
    @ns_result.doc('get_result', params={
        'job_name': 'Jenkins job name',
        'build_id': 'Jenkins build number',
        'case_name': 'Jenkins test case name'
    }
    )
    def get(self, job_name, build_id, case_name):
        """Get result by job_name and build_id"""
        msg = service.ResultApi.read_all(job_name=job_name,
                                         build_id=build_id, case_name=case_name)
        return jsonify(msg)


@ns_result.route("/result")
class ResultPost(Resource):
    @ns_result.expect(result_model)
    @ns_result.doc('create_result')
    def post(self):
        """Create a new result"""
        data = request.json
        msg, code = service.ResultApi.create(data)
        return msg, code


@ns_result.route("/result/<string:job_name>/<string:build_id>")
class ResultDeleteAll(Resource):
    @ns_result.expect(result_model)
    @ns_result.doc('update_result', params={
        'job_name': 'Jenkins job name',
        'build_id': 'Jenkins build number'
    })
    def put(self, job_name, build_id):
        """Update an existing result"""
        data = request.json
        msg, code = service.ResultApi.update_one(data,
                                                 job_name=job_name,
                                                 build_id=build_id)
        return msg, code

    @ns_result.doc('delete_result', params={
        'job_name': 'Jenkins job name',
        'build_id': 'Jenkins build number'
    })
    def delete(self, job_name, build_id):
        """Delete a result"""
        msg, code = service.ResultApi.delete(job_name=job_name,
                                             build_id=build_id)
        return msg, code


@ns_result.route("/result/<string:job_name>/<string:build_id>/<string"
                 ":case_name>")
class ResultDeleteOne(Resource):
    @ns_result.expect(result_model)
    @ns_result.doc('update_result', params={
        'job_name': 'Jenkins job name',
        'build_id': 'Jenkins build number'
    })
    def put(self, job_name, build_id, case_name):
        """Update an existing result"""
        data = request.json
        msg, code = service.ResultApi.update_one(data,
                                                 job_name=job_name,
                                                 build_id=build_id,
                                                 case_name=case_name)
        return msg, code

    @ns_result.doc('delete_result', params={
        'job_name': 'Jenkins job name',
        'build_id': 'Jenkins build number'
    })
    def delete(self, job_name, build_id, case_name):
        """Delete a result"""
        msg, code = service.ResultApi.delete(job_name=job_name,
                                             build_id=build_id,
                                             case_name=case_name)
        return msg, code


# Define Counter API endpoint under the 'ns_result' namespace
@ns_result.route("/log/counter/<string:job_name>/<string:build_id>"
                 "/<string:case_name>/<string:counter>")
class Counter(Resource):
    @ns_result.doc('get_counter', params={
        'job_name': 'Jenkins job name',
        'build_id': 'Jenkins build number',
        'case_name': 'Test case name',
        'counter': 'Performance counter'
    })
    def get(self, job_name, build_id, counter, case_name):
        """Get counter log by job_name, build_id, counter, and case_name"""
        msg = service.CounterApi.read_all(
            job_name=job_name,
            build_id=build_id,
            counter=counter,
            case_name=case_name
        )
        return jsonify(msg)


@ns_result.route("/log/counter")
class CounterPost(Resource):
    @ns_result.expect(counter_model)
    @ns_result.doc('create_counter')
    def post(self):
        """Create a new counter log"""
        data = request.json
        status_code = 201
        resp_msg = None
        for d in data["data"]:
            msg, code = service.CounterApi.create(d)
            if code > status_code:
                status_code = code
                resp_msg = msg
        return resp_msg, status_code


@ns_result.route("/log/counter/<string:job_name>/<string:build_id>")
class CounterDelete(Resource):
    @ns_result.doc('delete_counter', params={
        'job_name': 'Jenkins job name',
        'build_id': 'Jenkins build number'
    })
    def delete(self, job_name, build_id):
        """Delete a counter log"""
        msg, code = service.CounterApi.delete(
            job_name=job_name,
            build_id=build_id)
        return msg, code


# Define CrashLog API endpoint under the 'ns_result' namespace
@ns_result.route("/log/crash/<string:job_name>"
                 "/<string:build_id>/<string:case_name>")
class CrashLog(Resource):
    @ns_result.doc('get_crash_log', params={
        'job_name': 'Jenkins job name',
        'build_id': 'Jenkins build number',
        'case_name': 'Test case name'
    })
    def get(self, job_name, build_id, case_name):
        """Get crash log by job_name, build_id, and case_name"""
        msg = service.CrashLogApi.read_all(
            job_name=job_name,
            build_id=build_id,
            case_name=case_name
        )
        return jsonify(msg)


@ns_result.route("/log/crash")
class CrashLogPost(Resource):
    @ns_result.expect(log_model)
    @ns_result.doc('create_crash_log')
    def post(self):
        """Create a new crash log"""
        data = request.json
        msg, code = service.CrashLogApi.create(data)
        return msg, code


@ns_result.route("/log/crash/<string:job_name>/<string:build_id>")
class CrashLogPost(Resource):
    @ns_result.doc('delete_crash_log', params={
        'job_name': 'Jenkins job name',
        'build_id': 'Jenkins build number'
    })
    def delete(self, job_name, build_id):
        """Delete a crash log"""
        msg, code = service.CrashLogApi.delete(job_name=job_name, build_id=build_id)
        return msg, code


# Define ConsoleLog API endpoint under the 'ns_result' namespace
@ns_result.route("/log/console/<string:job_name>"
                 "/<string:build_id>/<string:case_name>")
class ConsoleLog(Resource):
    @ns_result.doc('get_console_log', params={
        'job_name': 'Jenkins job name',
        'build_id': 'Jenkins build number',
        'case_name': 'Test case name'
    })
    def get(self, job_name, build_id, case_name):
        """Get console log by job_name, build_id, and case_name"""
        msg = service.ConsoleLogApi.read_all(
            job_name=job_name,
            build_id=build_id,
            case_name=case_name
        )
        return jsonify(msg)


@ns_result.route("/log/console")
class ConsoleLogPost(Resource):
    @ns_result.expect(log_model)
    @ns_result.doc('create_console_log')
    def post(self):
        """Create a new console log"""
        data = request.json
        msg, code = service.ConsoleLogApi.create(data)
        return msg, code


@ns_result.route("/log/console/<string:job_name>/<string:build_id>")
class ConsoleLogDelete(Resource):
    @ns_result.doc('delete_console_log', params={
        'job_name': 'Jenkins job name',
        'build_id': 'Jenkins build number'
    })
    def delete(self, job_name, build_id):
        """Delete a console log"""
        msg, code = service.ConsoleLogApi.delete(
            job_name=job_name, build_id=build_id
        )
        return msg, code


# Define CommandLog API endpoint under the 'ns_result' namespace
@ns_result.route("/log/command/<string:job_name>"
                 "/<string:build_id>/<string:case_name>")
class CommandLog(Resource):
    @ns_result.doc('get_command_log', params={
        'job_name': 'Jenkins job name',
        'build_id': 'Jenkins build number',
        'case_name': 'Test case name'
    })
    def get(self, job_name, build_id, case_name):
        """Get command log by job_name, build_id, and case_name"""
        msg = service.CommandLogApi.read_all(
            job_name=job_name,
            build_id=build_id,
            case_name=case_name
        )
        return jsonify(msg)


@ns_result.route("/log/command/<string:job_name>/<string:build_id>")
class CommandLogDelete(Resource):
    @ns_result.doc('delete_command_log', params={
        'job_name': 'Jenkins job name',
        'build_id': 'Jenkins build number'})
    def delete(self, job_name, build_id):
        """Delete a command log"""
        msg, code = service.CommandLogApi.delete(
            job_name=job_name,
            build_id=build_id
        )
        return msg, code


@ns_result.route("/log/command")
class CommandLogPost(Resource):
    @ns_result.expect(log_model)
    @ns_result.doc('create_command_log')
    def post(self):
        """Create a new command log"""
        data = request.json
        msg, code = service.CommandLogApi.create(data)
        return msg, code


# Define Task API endpoint under the 'ns_result' namespace
@ns_result.route("/task/<string:job_name>")
class Task(Resource):
    @ns_result.doc('get_task_status', params={'job_name': 'Jenkins job name'})
    def get(self, job_name):
        """Get task status by job_name"""
        msg = check_job_status(job_name)
        return msg, 200 if msg else 404
