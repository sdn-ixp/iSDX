{
    "outbound": [
        {
            "cookie": 1,
            "match": 
            {
                "tcp_dst": 80
            },
            "action": 
            {
                "fwd": 2
            }
        },
        {
            "cookie": 2,
            "match": 
            {
                "tcp_dst": 4321
            },
            "action": 
            {
                "fwd": 3
            }
        },
        {
            "cookie": 3,
            "match": 
            {
                "tcp_dst": 4322
            },
            "action": 
            {
                "fwd": 3
            }
        }
    ]
}
