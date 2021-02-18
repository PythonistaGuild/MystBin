import styles from "../styles/Dash.module.css";
import AccountCircleIcon from "@material-ui/icons/AccountCircle";
import ListIcon from "@material-ui/icons/List";
import FavoriteIcon from "@material-ui/icons/Favorite";
import ExitToAppIcon from "@material-ui/icons/ExitToApp";
import {Form, Button, Badge} from "react-bootstrap";
import {PropsWithoutRef, useState} from "react";
import DiscordColorIcon from "../icons/DiscordColour";
import GitHubIcon from "@material-ui/icons/GitHub";
import GoogleIcon from "../icons/GoogleIcon";
import BeenhereIcon from "@material-ui/icons/Beenhere";
import AddBoxIcon from "@material-ui/icons/AddBox";
import {XGrid, RowsProp, ColDef, LicenseInfo, CellParams} from '@material-ui/x-grid';
import { Collapse } from '@material-ui/core';
import PeopleIcon from '@material-ui/icons/People';
import AssignmentIcon from '@material-ui/icons/Assignment';
import BubbleChartIcon from '@material-ui/icons/BubbleChart';
import {display} from "@material-ui/system";
import PatreonFireyIcon from "../icons/PatreonFirey";
import {useRouter} from "next/router";
import Cookies from "cookies";
import SleeperPush from "../components/Sleeper";


export default function Discord_auth(props: PropsWithoutRef<{ payload }>) {
  const {payload} = props;
  const admin = payload['admin'];

  const [tokenRevealed, setTokenRevealed] = useState(false);
  const [themeSelected, setThemeSelected] = useState("dark");
  const [selectedTab, setSelectedTab] = useState(0);

  const standardPasteColumns: ColDef[] = [
    { field: 'id', headerName: "ID", width: 250},
    { field: 'file_count', headerName: 'Files', width: 100},
    { field: 'created_at', headerName: 'Created at', resizable: true, width: 200},
    { field: 'expires', headerName: 'Expiry', resizable: true, width: 200 },
    { field: 'password', headerName: 'Password'},
    { field: 'views', headerName: 'Views'},
    { field: 'delete', headerName: 'Delete', width: 125, renderCell: (params: CellParams) => (<h5><Badge className={styles.tableRowDelete} variant={"danger"}>Delete Paste</Badge></h5>)}
  ];

  const standardPasteRows: RowsProp = [
    { id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},
    { id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},
    { id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},{ id: "ThreeRandomWords", file_count: 3, created_at: 'Datetime', expires: "Datetime", password: 'True', views: 666},

  ];


  return (
      <>
    <div className={styles.container}>
      <div className={styles.sideNav}>
        <div className={styles.sideButton} style={selectedTab === 0 ? {backgroundColor: "rgba(255, 255, 255, 0.2)"} : {}} onClick={() => {setSelectedTab(0)}}>
          <AccountCircleIcon />
          <span className={styles.buttonText}>Account Settings</span>
        </div>
        <div className={styles.sideButton} style={selectedTab === 1 ? {backgroundColor: "rgba(255, 255, 255, 0.2)"} : {}} onClick={() => {setSelectedTab(1)}}>
          <ListIcon />
          <span className={styles.buttonText}>Manage Pastes</span>
        </div>
        <div className={styles.sideButton} style={selectedTab === 2 ? {backgroundColor: "rgba(255, 255, 255, 0.2)"} : {}} onClick={() => {setSelectedTab(2)}}>
          <FavoriteIcon />
          <span className={styles.buttonText}>Bookmarks</span>
        </div>

        {!!admin ?
            <>
            <div className={styles.sideButton} style={selectedTab === 3 ? {backgroundColor: "rgba(255, 255, 255, 0.2)"} : {}} onClick={() => {setSelectedTab(3)}}>
              <PeopleIcon />
              <span className={styles.buttonText}>Admin - Users</span>
            </div>
              <div className={styles.sideButton} style={selectedTab === 4 ? {backgroundColor: "rgba(255, 255, 255, 0.2)"} : {}} onClick={() => {setSelectedTab(4)}}>
                <AssignmentIcon />
                <span className={styles.buttonText}>Admin - Pastes</span>
              </div>
              <div className={styles.sideButton} style={selectedTab === 5 ? {backgroundColor: "rgba(255, 255, 255, 0.2)"} : {}} onClick={() => {setSelectedTab(5)}}>
                <BubbleChartIcon />
                <span className={styles.buttonText}>Admin - Analytics</span>
              </div>
            </>
            : {}}

        <div className={styles.exitButton}>
          <ExitToAppIcon />
          <span className={styles.buttonText}>Return to site</span>
        </div>
      </div>

      <div className={styles.accountDetails} style={selectedTab === 0 ? {} : {display: "none"}}>
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
              <span className={styles.tokenRevealed}>
                isuf8u2
                n87f2n2nf98n29fn92n9fn2983fn9283nf98n239fn32ff98n329fn923nf9n239f8n923nfurhfguhefbgjdfvlkdfnvposnocwc9idh9q8h23riubweejfbiusdbf887gfuywebfui
              </span>
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
            <h6>Subscriber:</h6>Not Subscribed :(
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
          ></div>
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
          ></div>
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

      <div className={styles.tableContainer} style={selectedTab === 1 ? {} : {display: "none"}}>
        <XGrid
          checkboxSelection={false}
          columns={standardPasteColumns}
          rows={standardPasteRows}
          pagination={true}
          rowsPerPageOptions={[50, 100, 250, 500, 1000]}
        >
        </XGrid>
      </div>

      <div className={styles.tableContainer} style={selectedTab === 2 ? {} : {display: "none"}}>
        <XGrid
            checkboxSelection={false}
            columns={standardPasteColumns}
            rows={standardPasteRows}
            pagination={true}
            rowsPerPageOptions={[50, 100, 250, 500, 1000]}
        >
        </XGrid>
      </div>

      {!!admin ?
          <>
            <div className={styles.tableContainer} style={selectedTab === 3 ? {} : {display: "none"}}>
              <XGrid
                  checkboxSelection={false}
                  columns={standardPasteColumns}
                  rows={standardPasteRows}
                  pagination={true}
                  rowsPerPageOptions={[50, 100, 250, 500, 1000]}
              >
              </XGrid>
            </div>
            <div className={styles.tableContainer} style={selectedTab === 4 ? {} : {display: "none"}}>
              <XGrid
                  checkboxSelection={false}
                  columns={standardPasteColumns}
                  rows={standardPasteRows}
                  pagination={true}
                  rowsPerPageOptions={[50, 100, 250, 500, 1000]}
              >
              </XGrid>
            </div>
          <div className={styles.accountDetails} style={selectedTab === 5 ? {} : {display: "none"}}>
            <h4 className={styles.headerFullWidthFlex}>Server Details</h4>
            <div className={styles.innerEmbedFlexCol}>
              <h5>Memory</h5>300Mb

            </div>
          </div>
          </>
      :
          {}
      }
    </div>
      </>
  );
}

export const getServerSideProps = async ({ req, res, query }) => {
  const cookies = new Cookies(req, res);
  const token = cookies.get("auth");

  let analyticsData =  null;

  const resp = await fetch("http://api:9000/users/me", {
    method: "GET",
    headers: { "Authorization": `Bearer ${token}`, "Content-Type": "application/json" },
  });

  if (resp.status !== 200) {
    cookies.set('state');
    cookies.set('auth');

    return {
      redirect: {
        destination: '/',
        permanent: false,
      },
    }
  }

  let payload = {};
  let data = await resp.json();
  const admin = data["admin"];

  if (!!admin) {
    const analyticsResp = await fetch("http://api:9000/admin/stats", {
      method: "GET",
      headers: { "Authorization": `Bearer ${token}` }
    });

    analyticsData = await analyticsResp.json();
  }

  console.debug('HERE!');
  payload["admin"] = data["admin"];
  payload["analytics"] = analyticsData;
  console.debug(payload);
  return { props: { payload }, };
};