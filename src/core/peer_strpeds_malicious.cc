
#include "peer_strpeds_malicious.h"

namespace p2psp {
void PeerStrpeDsMalicious::Init() { LOG("Initialized"); }

void PeerStrpeDsMalicious::SetBadMouthAttack(
    bool value, std::vector<ip::udp::endpoint> selected) {
  bad_mouth_attack_ = value;

  if (value) {
    bad_peers_.insert(bad_peers_.end(), selected.begin(), selected.end());
  } else {
    bad_peers_.clear();
  }
}

void PeerStrpeDsMalicious::SetSelectiveAttack(
    bool value, std::vector<ip::udp::endpoint> selected) {
  selective_attack_ = true;

  selected_peers_for_attack_.insert(selected_peers_for_attack_.end(),
                                    selected.begin(), selected.end());
}
}