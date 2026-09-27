"""Industries: index list, members, snapshot with the pre-market caveat.

Run:  python examples/04_industries.py
"""

import algotik_tse as att


def main():
    indices = att.list_industry_indices(progress=False)
    print("industry indices:", len(indices))

    # Membership is served by ClosingPrice/GetIndexCompany, which TSETMC
    # empties outside publication windows. Keep empty rows visible and
    # read attrs instead of assuming.
    members = att.get_industry_members("فلزات اساسی", include_live=True,
                                       progress=False)
    print("basic-metals members:", len(members))

    snapshot = att.get_industry_snapshot(["فلزات اساسی", "بانک"],
                                         include_empty=True, progress=False)
    print("snapshot rows:", len(snapshot))
    print("empty industries in attrs:",
          snapshot.attrs.get("empty_industries"))

    ranking = att.rank_industries(progress=False)
    print("ranked industries:", len(ranking))


if __name__ == "__main__":
    main()
