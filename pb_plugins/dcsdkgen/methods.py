# -*- coding: utf-8 -*-
from .utils import (remove_subscribe,
                    filter_out_result,
                    no_return,
                    is_stream,
                    Param,
                    type_info_factory)
from .name_parser import NameParser


class Method(object):
    """ Method """

    def __init__(
            self,
            plugin_name,
            package,
            pb_method,
            requests,
            responses):
        self._plugin_name = NameParser(plugin_name)
        self._package = NameParser(package)
        self._name = NameParser(pb_method.name)
        self.extract_params(pb_method, requests)
        self.extract_return_type_and_name(pb_method, responses)
        self._is_stream = False
        self._no_return = False
        self._returns = False

    def extract_params(self, pb_method, requests):
        method_input = pb_method.input_type.split(".")[-1]
        request = requests[method_input]

        self._params = []

        for field in request.field:
            self._params.append(
                Param(
                    name=NameParser(field.name),
                    type_info=type_info_factory.create(field))
            )

    def extract_return_type_and_name(self, pb_method, responses):
        method_output = pb_method.output_type.split(".")[-1]
        response = responses[method_output]

        return_params = list(filter_out_result(response.field))

        if len(return_params) > 1:
            raise Exception(
                "Responses cannot have more than 1 return parameter" +
                f"(and an optional '*Result')!\nError in {method_output}")

        if len(return_params) == 1:
            self._return_type = type_info_factory.create(return_params[0])
            self._return_name = NameParser(return_params[0].json_name)

    @property
    def is_stream(self):
        return self._is_stream

    @property
    def no_return(self):
        return self._no_return

    @property
    def returns(self):
        return self._returns

    @property
    def plugin_name(self):
        return self._plugin_name

    @property
    def package(self):
        return self._package

    @property
    def name(self):
        return self._name

    @staticmethod
    def collect_methods(
            plugin_name,
            package,
            methods,
            structs,
            requests,
            responses,
            template_env):
        """ Collects all methods for the plugin """
        _methods = {}
        for method in methods:
            # Check if method is just a call
            if (no_return(method, responses)):
                _methods[method.name] = Call(plugin_name,
                                             package,
                                             template_env,
                                             method,
                                             requests,
                                             responses)

            # Check if stream
            elif (is_stream(method)):
                _methods[method.name] = Stream(plugin_name,
                                               package,
                                               template_env,
                                               method,
                                               requests,
                                               responses)

            else:
                _methods[method.name] = Request(plugin_name,
                                                package,
                                                template_env,
                                                method,
                                                requests,
                                                responses)

        return _methods

    def __repr__(self):
        return "method: {}".format(self._name)


class Call(Method):
    """ A call method doesn't return any value, but either succeeds or fails
    """

    def __init__(
            self,
            plugin_name,
            package,
            template_env,
            pb_method,
            requests,
            responses):
        super().__init__(plugin_name, package, pb_method, requests, responses)
        self._template = template_env.get_template("call.j2")
        self._no_return = True

    def __repr__(self):
        return self._template.render(name=self._name,
                                     params=self._params,
                                     plugin_name=self._plugin_name,
                                     package=self._package)


class Request(Method):
    """ Requests a value """

    def __init__(
            self,
            plugin_name,
            package,
            template_env,
            pb_method,
            requests,
            responses):
        super().__init__(plugin_name, package, pb_method, requests, responses)
        self._template = template_env.get_template("request.j2")
        self._returns = True

    def __repr__(self):
        return self._template.render(
            name=self._name,
            params=self._params,
            return_type=self._return_type,
            return_name=self._return_name,
            plugin_name=self._plugin_name,
            package=self._package)


class Stream(Method):
    """ A stream of values """

    def __init__(
            self,
            plugin_name,
            package,
            template_env,
            pb_method,
            requests,
            responses):
        super().__init__(plugin_name, package, pb_method, requests, responses)
        self._name = NameParser(remove_subscribe(pb_method.name))
        self._template = template_env.get_template("stream.j2")
        self._is_stream = True

    def __repr__(self):
        return self._template.render(
            name=self._name,
            params=self._params,
            return_type=self._return_type,
            return_name=self._return_name,
            plugin_name=self._plugin_name,
            package=self._package)
