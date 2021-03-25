import styles from "../styles/Dash.module.css";
import AccountCircleIcon from "@material-ui/icons/AccountCircle";
import ListIcon from "@material-ui/icons/List";
import FavoriteIcon from "@material-ui/icons/Favorite";
import ExitToAppIcon from "@material-ui/icons/ExitToApp";
import { Form, Button, Badge } from "react-bootstrap";
import { PropsWithoutRef, useState } from "react";
import DiscordColorIcon from "../icons/DiscordColour";
import GitHubIcon from "@material-ui/icons/GitHub";
import GoogleIcon from "../icons/GoogleIcon";
import BeenhereIcon from "@material-ui/icons/Beenhere";
import AddBoxIcon from "@material-ui/icons/AddBox";
import {
  XGrid,
  RowsProp,
  ColDef,
  LicenseInfo,
  CellParams,
  RowParams,
} from "@material-ui/x-grid";
import { Collapse } from "@material-ui/core";
import PeopleIcon from "@material-ui/icons/People";
import AssignmentIcon from "@material-ui/icons/Assignment";
import BubbleChartIcon from "@material-ui/icons/BubbleChart";
import Cookies from "cookies";
import PrettySeconds from "../components/PrettySeconds";
import cookieCutter from "cookie-cutter";

export default function Test(props) {
  const { admin, token, analytics, initialAdminPastes, subscriber } = props;

  const [tokenRevealed, setTokenRevealed] = useState(false);
  const [themeSelected, setThemeSelected] = useState("dark");
  const [selectedTab, setSelectedTab] = useState(0);

  const [adminPasteRows, setAdminPasteRows] = useState(
    initialAdminPastes["pastes"]
  );
  const [adminPasteLoading, setAdminPasteLoading] = useState(false);

  const adminTotalPastes = analytics["total_pastes"];

  const standardPasteColumns: ColDef[] = [
    { field: "id", headerName: "ID", width: 250 },
    { field: "file_count", headerName: "Files", width: 100 },
    {
      field: "created_at",
      headerName: "Created at",
      resizable: true,
      width: 200,
    },
    { field: "expires", headerName: "Expiry", resizable: true, width: 200 },
    { field: "password", headerName: "Password" },
    { field: "views", headerName: "Views" },
    {
      field: "delete",
      headerName: "Delete",
      width: 125,
      renderCell: (params: CellParams) => (
        <h5>
          <Badge className={styles.tableRowDelete} variant={"danger"}>
            Delete Paste
          </Badge>
        </h5>
      ),
    },
  ];
  let subscribertext = "";
  if (subscriber) {
    subscribertext = "Subscribed :)";
  } else {
    subscribertext = "Not Subscribed :(";
  }

  const realPasteColumns: ColDef[] = [
    { field: "id", headerName: "ID", width: 250 },
    { field: "author_id", headerName: "Author ID", width: 240 },
    {
      field: "created_at",
      headerName: "Created at",
      resizable: true,
      width: 240,
    },
    { field: "expires", headerName: "Expiry", resizable: true, width: 240 },
    { field: "has_password", headerName: "Password" },
    { field: "views", headerName: "Views" },
    { field: "origin_ip", headerName: "IP Addr" },
    {
      field: "delete",
      headerName: "Delete",
      width: 125,
      renderCell: (params: CellParams) => (
        <h5>
          <Badge className={styles.tableRowDelete} variant={"danger"}>
            Delete Paste
          </Badge>
        </h5>
      ),
    },
  ];

  const standardPasteRows: RowsProp = [
    {
      id: "ThreeRandomWords",
      file_count: 3,
      created_at: "Datetime",
      expires: "Datetime",
      password: "True",
      views: 666,
    },
  ];

  return (
    <>
      <div className={styles.container}>
        <div className={styles.sideNav}>
          <div
            className={styles.sideButton}
            style={
              selectedTab === 0
                ? { backgroundColor: "rgba(255, 255, 255, 0.2)" }
                : null
            }
            onClick={() => {
              setSelectedTab(0);
            }}
          >
            <AccountCircleIcon />
            <span className={styles.buttonText}>Account Settings</span>
          </div>
          <div
            className={styles.sideButton}
            style={
              selectedTab === 1
                ? { backgroundColor: "rgba(255, 255, 255, 0.2)" }
                : null
            }
            onClick={() => {
              setSelectedTab(1);
            }}
          >
            <ListIcon />
            <span className={styles.buttonText}>Manage Pastes</span>
          </div>
          <div
            className={styles.sideButton}
            style={
              selectedTab === 2
                ? { backgroundColor: "rgba(255, 255, 255, 0.2)" }
                : null
            }
            onClick={() => {
              setSelectedTab(2);
            }}
          >
            <FavoriteIcon />
            <span className={styles.buttonText}>Bookmarks</span>
          </div>

          {!!admin ? (
            <>
              <div
                className={styles.sideButton}
                style={
                  selectedTab === 3
                    ? { backgroundColor: "rgba(255, 255, 255, 0.2)" }
                    : null
                }
                onClick={() => {
                  setSelectedTab(3);
                }}
              >
                <PeopleIcon />
                <span className={styles.buttonText}>Admin - Users</span>
              </div>
              <div
                className={styles.sideButton}
                style={
                  selectedTab === 4
                    ? { backgroundColor: "rgba(255, 255, 255, 0.2)" }
                    : null
                }
                onClick={() => {
                  setSelectedTab(4);
                }}
              >
                <AssignmentIcon />
                <span className={styles.buttonText}>Admin - Pastes</span>
              </div>
              <div
                className={styles.sideButton}
                style={
                  selectedTab === 5
                    ? { backgroundColor: "rgba(255, 255, 255, 0.2)" }
                    : null
                }
                onClick={() => {
                  setSelectedTab(5);
                }}
              >
                <BubbleChartIcon />
                <span className={styles.buttonText}>Admin - Analytics</span>
              </div>
            </>
          ) : null}

          <div className={styles.exitButton}>
            <ExitToAppIcon />
            <span className={styles.buttonText}>Return to site</span>
          </div>
        </div>

        <div
          className={styles.accountDetails}
          style={selectedTab === 0 ? null : { display: "none" }}
        >
          <h4 className={styles.headerFullWidthFlex}>Account Details</h4>
          <br />
          <div className={styles.embededData}>
            <div className={styles.innerEmbedFlexCol}>
              <h6>Account ID:</h6>2396858253982753
            </div>
            <Button variant="primary" className={styles.copyButton}>
              Copy
            </Button>
          </div>
          <div className={styles.embededData}>
            <div className={styles.innerEmbedFlexCol}>
              <h6>API Token:</h6>
              {!tokenRevealed ? (
                <span
                  className={styles.tokenReveal}
                  onClick={() => {
                    setTokenRevealed(true);
                  }}
                >
                  Click to reveal
                </span>
              ) : (
                <span className={styles.tokenRevealed}>{token}</span>
              )}
            </div>

            <Button variant="info" className={styles.copyButton}>
              Regenerate
            </Button>
            <Button variant="primary" className={styles.copyButton}>
              Copy
            </Button>
          </div>
          <div className={styles.embededData}>
            <div className={styles.innerEmbedFlexCol}>
              <h6>Subscriber:</h6>
              {subscribertext}
            </div>
          </div>

          <h4 className={styles.headerFullWidthFlex}>Theme Options</h4>

          <div
            className={styles.themeOptionDivDark}
            onClick={() => {
              setThemeSelected("dark");
            }}
          >
            <h4 style={{ marginTop: "1rem" }}>Dark</h4>
            <div
              className={
                themeSelected === "dark"
                  ? styles.radioCheckDarkSelected
                  : styles.radioCheckDark
              }
              onClick={() => {
                setThemeSelected("dark");
              }}
            />
          </div>

          <div
            className={styles.themeOptionDivLight}
            onClick={() => {
              setThemeSelected("light");
            }}
          >
            <h4 style={{ marginTop: "1rem" }}>Light</h4>
            <div
              className={
                themeSelected === "light"
                  ? styles.radioCheckLightSelected
                  : styles.radioCheckLight
              }
              onClick={() => {
                setThemeSelected("light");
              }}
            />
          </div>

          <h4 className={styles.headerFullWidthFlex}>Linked Logins</h4>
          <div className={styles.embededDataLogin}>
            <div className={styles.innerLoginEmbed}>
              <h5>Discord</h5>
              <DiscordColorIcon
                style={{ fontSize: "6rem", marginBottom: "-0.75rem" }}
              />
              <BeenhereIcon className={styles.loginConfirmed} />
              Account linked
            </div>
          </div>

          <div className={styles.embededDataLogin}>
            <div className={styles.innerLoginEmbed}>
              <h5>GitHub</h5>
              <GitHubIcon style={{ fontSize: "5.25rem" }} />
              <BeenhereIcon className={styles.loginConfirmed} />
              Account linked
            </div>
          </div>

          <div className={styles.embededDataLogin}>
            <div className={styles.innerLoginEmbed}>
              <h5>Google</h5>
              <GoogleIcon style={{ height: "5.25rem" }} />
              <AddBoxIcon className={styles.loginAddButton} />
              Link this account
            </div>
          </div>
        </div>

        <div
          className={styles.tableContainer}
          style={selectedTab === 1 ? null : { display: "none" }}
        >
          <XGrid
            checkboxSelection={false}
            columns={standardPasteColumns}
            rows={standardPasteRows}
            pagination={true}
            rowsPerPageOptions={[50, 100, 250, 500, 1000]}
          />
        </div>

        <div
          className={styles.tableContainer}
          style={selectedTab === 2 ? null : { display: "none" }}
        >
          <XGrid
            checkboxSelection={false}
            columns={standardPasteColumns}
            rows={standardPasteRows}
            pagination={true}
            rowsPerPageOptions={[50, 100, 250, 500, 1000]}
          />
        </div>

        {!!admin ? (
          <>
            <div
              className={styles.tableContainer}
              style={selectedTab === 3 ? null : { display: "none" }}
            >
              <XGrid
                checkboxSelection={false}
                columns={standardPasteColumns}
                rows={standardPasteRows}
                pagination={true}
                rowsPerPageOptions={[50, 100, 250, 500, 1000]}
              />
            </div>
            <div
              className={styles.tableContainer}
              style={selectedTab === 4 ? null : { display: "none" }}
            >
              <XGrid
                checkboxSelection
                columns={realPasteColumns}
                rows={adminPasteRows}
                pagination={true}
                rowsPerPageOptions={[25, 50, 100]}
                pageSize={100}
                rowCount={adminTotalPastes}
                paginationMode={"server"}
                filterMode={"server"}
                loading={adminPasteLoading}
                onFilterModelChange={(param) => {
                  setAdminPasteLoading(true);

                  fetch(
                    "https://api-staging.mystb.in/admin/pastes?page=0&count=999999999",
                    {
                      method: "GET",
                      headers: { Authorization: `Bearer ${token}` },
                    }
                  )
                    .then((r) => r.json())
                    .then((d) => {
                      const newRows = d.pastes.filter(
                        (p) =>
                          !!p.id
                            .toLowerCase()
                            .includes(param.filterModel.items[0].value)
                      );
                      setAdminPasteRows(newRows);
                      setAdminPasteLoading(false);
                    });
                }}
                onPageChange={(param) => {
                  setAdminPasteLoading(true);

                  fetch(
                    "https://api-staging.mystb.in/admin/pastes?count=100&page=" +
                      param.page,
                    {
                      method: "GET",
                      headers: { Authorization: `Bearer ${token}` },
                    }
                  )
                    .then((r) => r.json())
                    .then((d) => {
                      setAdminPasteRows(d["pastes"]);
                      setAdminPasteLoading(false);
                    });
                }}
              />
            </div>
            <div
              className={styles.accountDetails}
              style={selectedTab === 5 ? null : { display: "none" }}
            >
              <h4 className={styles.headerFullWidthFlex}>Server Controls</h4>

              <div className={styles.embededData}>
                <div className={styles.innerEmbedFlexCol}>
                  <h5>Git Pull</h5>This will pull and update from "main" on
                  GitHub. Please make sure any changes are tested before using
                  this command.
                </div>
                <Button variant={"info"} className={styles.copyButton}>
                  Confirm
                </Button>
              </div>

              <div className={styles.embededData}>
                <div className={styles.innerEmbedFlexCol}>
                  <h5>Restart Stack</h5>This will rebuild MystBin and update any
                  changes fetched via GitHub. Please make sure you have tested
                  any changes before using this command.
                </div>
                <Button variant={"danger"} className={styles.copyButton}>
                  Confirm
                </Button>
              </div>

              <h4 className={styles.headerFullWidthFlex}>Server Performance</h4>

              <div className={styles.embededData}>
                <div className={styles.innerEmbedFlexCol}>
                  <h5>Memory:</h5>
                  {analytics["memory"].toFixed(2)} MiB
                </div>
              </div>

              <div className={styles.embededData}>
                <div className={styles.innerEmbedFlexCol}>
                  <h5>Memory %:</h5>
                  {analytics["memory_percent"].toFixed(2)} %
                </div>
              </div>

              <div className={styles.embededData}>
                <div className={styles.innerEmbedFlexCol}>
                  <h5>CPU %:</h5>
                  {analytics["cpu_percent"].toFixed(2)} %
                </div>
              </div>

              <h4 className={styles.headerFullWidthFlex}>General Usage</h4>

              <div className={styles.embededData}>
                <div className={styles.innerEmbedFlexCol}>
                  <h5>Total Pastes:</h5>
                  {analytics["total_pastes"]}
                </div>
              </div>

              <div className={styles.embededData}>
                <div className={styles.innerEmbedFlexCol}>
                  <h5>Requests since Up:</h5>
                  {analytics["requests"]}
                </div>
              </div>

              <div className={styles.embededData}>
                <div className={styles.innerEmbedFlexCol}>
                  <h5>Uptime:</h5>
                  <PrettySeconds seconds={analytics["uptime"]} />
                </div>
              </div>

              <h4 className={styles.headerFullWidthFlex}>Server Graphs</h4>

              <iframe
                src="https://metrics.mystb.in/d-solo/Es8N4GyGk/api?orgId=1&from=1613874854877&to=1613896454877&refresh=5s&panelId=2"
                width="49.5%"
                height="400"
                frameBorder="0"
              />
              <iframe
                src="https://metrics.mystb.in/d-solo/Es8N4GyGk/api?orgId=1&from=1613874922449&to=1613896522449&refresh=5s&panelId=4"
                width="49.5%"
                height="400"
                frameBorder="0"
              />
            </div>
          </>
        ) : null}
      </div>
    </>
  );
}

export const getServerSideProps = async ({ req, res, query }) => {
  const cookies = new Cookies(req, res);
  const token = cookies.get("auth");

  let analytics = {};
  let initialAdminPastes = {};

  const resp = await fetch("http://api:9000/users/me", {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });

  if (resp.status !== 200) {
    cookies.set("auth");

    return {
      redirect: {
        destination: "/",
        permanent: false,
      },
    };
  }

  let data = await resp.json();
  const admin = data["admin"];
  const subscriber = data["subscriber"];

  if (!!admin) {
    const analyticsResp = await fetch("http://api:9000/admin/stats", {
      method: "GET",
      headers: { Authorization: `Bearer ${token}` },
    });

    const initialPastes = await fetch("http://api:9000/admin/pastes?count=100&page=0", {
      method: "GET",
      headers: { Authorization: `Bearer ${token}` },
    });


    initialAdminPastes = await initialPastes.json();
    analytics = await analyticsResp.json();
  }

  return { props: { admin, token, analytics, initialAdminPastes, subscriber } };
};
