import json
from random import randint

from twisted.web import resource, http

from FakeTriblerAPI import tribler_utils


class TrustchainEndpoint(resource.Resource):

    def __init__(self):
        resource.Resource.__init__(self)

        child_handler_dict = {"statistics": TrustchainStatsEndpoint, "blocks": TrustchainBlocksEndpoint,
                              "network": TrustchainNetworkEndpoint}

        for path, child_cls in child_handler_dict.iteritems():
            self.putChild(path, child_cls())


class TrustchainStatsEndpoint(resource.Resource):
    """
    This class handles requests regarding the TrustChain community information.
    """

    def render_GET(self, request):
        last_block = tribler_utils.tribler_data.trustchain_blocks[-1]

        return json.dumps({'statistics': {
            "id": ('a' * 20).encode("hex"),
            "total_blocks": len(tribler_utils.tribler_data.trustchain_blocks),
            "total_down": last_block.total_down,
            "total_up": last_block.total_up,
            "peers_that_pk_helped": randint(10, 50),
            "peers_that_helped_pk": randint(10, 50),
            "latest_block": last_block.to_dictionary()
        }})

class TrustchainBlocksEndpoint(resource.Resource):
    """
    This class handles requests regarding the TrustChain community blocks.
    """

    def getChild(self, path, request):
        return TrustchainBlocksIdentityEndpoint(path)


class TrustchainBlocksIdentityEndpoint(resource.Resource):
    """
    This class represents requests for blocks of a specific identity.
    """

    def __init__(self, identity):
        resource.Resource.__init__(self)
        self.identity = identity

    def render_GET(self, request):
        """
        Return some random blocks
        """
        return json.dumps({"blocks": [block.to_dictionary() for block in tribler_utils.tribler_data.trustchain_blocks]})


class TrustchainNetworkEndpoint(resource.Resource):
    """
    Handle HTTP requests for trustchain network statistics.
    """

    isLeaf = True

    @staticmethod
    def return_error(request, status_code=http.BAD_REQUEST, message="your request seems to be wrong"):
        """
        Return a HTTP Code with the given message.

        :param request: the request which has to be changed
        :param status_code: the HTTP status code to be returned
        :param message: the error message which is used in the JSON string
        :return: the error message formatted in JSON
        """
        request.setResponseCode(status_code)
        return json.dumps({"error": message})

    def render_GET(self, request):
        """
        Process the GET request which retrieves the information used by the GUI Trust Display window.

        .. http:get:: /trustchain/network?focus_node=(string: public key)&neighbor_level=(int: neighbor_level)

        A GET request to this endpoint returns the data from the multichain. This data is retrieved from the multichain
        database and will be focused around the given focus node. The neighbor_level parameter specifies which nodes
        are taken into consideration (e.g. a neighbor_level of 2 indicates that only the focus node, it's neighbors
        and the neighbors of those neighbors are taken into consideration).

        Note: the parameters are handled as follows:
        - focus_node
            - Not given: HTTP 400
            - Non-String value: HTTP 400
            - "self": Multichain Community public key
            - otherwise: Passed data, albeit a string
        - neighbor_level
            - Not given: 1
            - Non-Integer value: 1
            - otherwise: Passed data, albeit an integer

        The returned data will be in such format that the GUI component which visualizes this data can easily use it.
        Although this data might not seem as formatted in a useful way to the human eye, this is done to accommodate as
        little parsing effort at the GUI side.

            **Example request**:
            .. sourcecode:: none

                curl -X GET http://localhost:8085/multichain/network?focus_node=xyz

            **Example response**:
            .. sourcecode:: javascript

                {
                    "focus_node": "xyz",
                    "neighbor_level: 1
                    "nodes": [{
                        "public_key": "xyz",
                        "total_up": 12736457,
                        "total_down": 1827364
                    }, ...],
                    "edges": [{
                        "from": "xyz",
                        "to": "xyz_n1",
                        "size": 12384
                    }, ...]
                }

        :param request: the HTTP GET request which specifies the focus node and optionally the neighbor level
        :return: the node data formatted in JSON
        """
        if "focus_node" not in request.args:
            return TrustchainNetworkEndpoint.return_error(request, message="focus_node parameter missing")

        if len(request.args["focus_node"]) < 1 or len(request.args["focus_node"][0]) == 0:
            return TrustchainNetworkEndpoint.return_error(request, message="focus_node parameter empty")

        focus_node = request.args["focus_node"][0]
        if not isinstance(focus_node, basestring) and not focus_node.lstrip("-").isdigit():
            return TrustchainNetworkEndpoint.return_error(request, message="focus_node was not a string")

        return json.dumps(tribler_utils.tribler_data.display_information)
