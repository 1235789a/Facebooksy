"""Quick self-test for Lead Radar scoring engine."""

from lead_radar.models import Lead
from lead_radar.scorer import score_lead, is_scam, score_and_filter_leads
from lead_radar.manual_import import quick_x_lead


def test_high_value_lead():
    lead = quick_x_lead(
        "alphawhaleguy",
        bio="Building the best Solana alpha Telegram group. Daily whale wallet alerts for my VIP members. 👇 t.me/alpha_whale_group",
        post_text="Just manually tracked 12 fresh wallets that bought $SOLPEPE early. Missed the first one but caught the rest with Dexscreener. Anyone else tracking smart money wallets? It's so hard to keep up manually. Join my Telegram for daily alpha calls - VIP for premium signals.",
        source_url="https://x.com/alphawhaleguy/status/123",
    )
    scored = score_lead(lead)
    assert scored.score >= 5, f"Expected >= 5, got {scored.score}"
    assert scored.community_signal
    assert scored.manual_workflow_signal
    assert scored.monetization_signal
    assert scored.pain_signal
    assert scored.type_guess != "unknown"
    assert scored.suggested_angle
    print(f"  PASS: high value lead scores {scored.score}/10 ({scored.type_guess})")
    print(f"        breakdown: {scored.score_breakdown}")


def test_newsletter_lead():
    lead = quick_x_lead(
        "cryptonewsqueen",
        bio="Weekly crypto newsletter | On-chain analyst | Sharing market updates and whale moves",
        post_text="This week's on-chain breakdown: 3 whale wallets accumulated $ETH over the weekend. I checked Arkham and Lookonchain manually to verify. Not sure if this is a trend or one-off. Need to check more wallets. My newsletter drops Friday - subscribe for the full report.",
    )
    scored = score_lead(lead)
    assert scored.score >= 4, f"Expected >= 4, got {scored.score}"
    assert "newsletter" in scored.type_guess.lower()
    assert scored.manual_workflow_signal
    print(f"  PASS: newsletter lead scores {scored.score}/10 ({scored.type_guess})")


def test_ordinary_trader_low_score():
    lead = quick_x_lead(
        "randomguy123",
        bio="just a guy trading crypto",
        post_text="bought some eth today, hope it goes up",
    )
    scored = score_lead(lead)
    assert scored.score < 5, f"Expected < 5, got {scored.score}"
    assert not scored.community_signal
    assert not scored.monetization_signal
    print(f"  PASS: ordinary trader scores {scored.score}/10 (correctly low)")


def test_scam_filter():
    scam_lead = quick_x_lead(
        "scambro",
        bio="100x guaranteed profit! free giveaway! click here! make money fast!",
        post_text="guaranteed profit 100x click here link in bio free airdrop",
    )
    assert is_scam(scam_lead), "Should be detected as scam"
    print(f"  PASS: scam lead correctly filtered")


def test_top_n():
    leads = []
    for i in range(15):
        lead = quick_x_lead(f"user{i}", bio="crypto trader", post_text=f"post {i}")
        leads.append(lead)
    top = score_and_filter_leads(leads, top_n=5)
    assert len(top) <= 5
    print(f"  PASS: top_n filter works ({len(top)} leads returned)")


def test_interactive_lead():
    lead = quick_x_lead(
        "communitymgr",
        bio="Community manager for Web3 project. Join our Discord!",
        post_text="What do you think about the new token launch? Let me know your thoughts in the comments. I've been manually checking wallets to see who's buying.",
    )
    scored = score_lead(lead)
    assert scored.interaction_signal or scored.score_breakdown["interaction"] > 0
    print(f"  PASS: interactive lead has interaction score: {scored.score_breakdown['interaction']}")


if __name__ == "__main__":
    print("Running Lead Radar self-tests...\n")
    test_high_value_lead()
    test_newsletter_lead()
    test_ordinary_trader_low_score()
    test_scam_filter()
    test_top_n()
    test_interactive_lead()
    print("\nAll tests passed! ✅")
