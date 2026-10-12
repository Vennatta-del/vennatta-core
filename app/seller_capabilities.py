"""Public payment capabilities derived from configured seller routes."""

def seller_capabilities(routes):
    networks_by_route = {
        name: sorted({str(option.network) for option in route.accepts})
        for name, route in sorted(routes.items())
    }
    networks = sorted({
        network
        for values in networks_by_route.values()
        for network in values
    })

    def label(network):
        if network == "eip155:8453":
            return "Base"
        if network.startswith("solana:"):
            return "Solana"
        return network

    return {
        "chains": sorted({label(network) for network in networks}),
        "payment_networks_by_route": networks_by_route,
    }
