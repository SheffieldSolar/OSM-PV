"""
Load REPD dataset from file into dataframe.
"""

import pandas as pd

from geocode import Geocoder

def load_repd(repd_filename, raw=False, cols=None):
    """
    Load the REPD dataset into a Pandas DataFrame.

    Parameters
    ----------
    `repd_filename` : string
        The filename (including path) to the REPD file. Set to None to prompt user to select
        file.
    `raw` : bool
        Set to True to return the raw data (i.e. without Geocoding, filtering). Useful if
        re-using this method in other code. Default is False.
    `cols` : list of strings
        Use in conjunction with `raw`=True to filter only certain columns. Useful if re-using
        this method in other code.

    Returns
    -------
    Pandas DataFrame
        A dataframe with columns: id, install_date, dc_capacity, funding_route, fit_registered,
        latitude, longitude, source.
    """
    df_raw = pd.read_excel(repd_filename, sheet_name="Database", header=6)
    repd = df_raw.loc[(df_raw["Technology Type"] == "Solar Photovoltaics") &
                      (df_raw["Country"] != "Northern Ireland")]
    if raw:
        if cols:
            repd = repd[cols]
        repd["id"] = repd.loc[:, "Ref ID"]
        return repd
    # repd = repd.assign(fit_registered=repd["FiT Tariff (p/kWh)"].notnull())
    repd = repd.assign(fit_registered=False).convert_dtypes() # FIT info in REPD is unreliable!
    repd = repd[["Ref ID", "Site Name", "Operational", "Installed Capacity (MWelec)", "X-coordinate",
                 "Y-coordinate", "Mounting Type for Solar", "fit_registered"]]
    col_mapper = {"Ref ID": "id", "Site Name": "site_name", "Operational": "install_date",
                  "Installed Capacity (MWelec)": "dc_capacity", "X-coordinate": "eastings",
                  "Y-coordinate": "northings", "fit_registered": "fit_registered",
                  "Mounting Type for Solar": "mounting_type"}
    repd.rename(columns=col_mapper, inplace=True)
    repd.reset_index(drop=True, inplace=True)
    repd = repd.assign(operational=repd.install_date.notnull())
    nn_indices = repd["eastings"].notnull()
    with Geocoder(quiet=True, progress_bar=False) as geo:
        lons, lats = geo.bng2latlon(repd.loc[(nn_indices, "eastings")].to_numpy(),
                                    repd.loc[(nn_indices, "northings")].to_numpy())
    repd.loc[nn_indices, "longitude"] = lons
    repd.loc[nn_indices, "latitude"] = lats
    repd.drop(columns=["eastings", "northings"], inplace=True)
    print(f"    -> Successfully loaded {len(repd.index)} PV systems from "
          f"'{repd_filename}'")
    repd = repd.assign(source="repd")
    repd = repd.assign(ground_mount=repd.mounting_type.str.contains("Ground"))
    return repd