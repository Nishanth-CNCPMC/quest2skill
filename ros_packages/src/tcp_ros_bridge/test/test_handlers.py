from tcp_ros_bridge.handlers import RightControllerHandler


def test_right_controller_handler_recognizes_current_payload():
    assert RightControllerHandler._looks_like_right_controller(
        {
            "right_detected": True,
            "origin_set": True,
            "rel_pos": [0.0, 0.0, 0.0],
            "rel_rot": [0.0, 0.0, 0.0, 1.0],
            "trigger": 0.5,
        }
    )


def test_vector_validation_rejects_wrong_size():
    assert RightControllerHandler._valid_vector([1.0, 2.0, 3.0], 3)
    assert not RightControllerHandler._valid_vector([1.0, 2.0], 3)
