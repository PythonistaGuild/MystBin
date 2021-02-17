import styles from "../styles/Dash.module.css";
import AccountCircleIcon from "@material-ui/icons/AccountCircle";
import ListIcon from "@material-ui/icons/List";
import FavoriteIcon from "@material-ui/icons/Favorite";
import ExitToAppIcon from "@material-ui/icons/ExitToApp";
import { Form, Button } from "react-bootstrap";
import { useState } from "react";
import DiscordColorIcon from "../icons/DiscordColour";
import GitHubIcon from "@material-ui/icons/GitHub";
import GoogleIcon from "../icons/GoogleIcon";
import BeenhereIcon from "@material-ui/icons/Beenhere";
import AddBoxIcon from "@material-ui/icons/AddBox";

export default function Discord_auth() {
  const [tokenRevealed, setTokenRevealed] = useState(false);
  const [themeSelected, setThemeSelected] = useState("dark");

  return (
    <div className={styles.container}>
      <div className={styles.sideNav}>
        <div className={styles.sideButton}>
          <AccountCircleIcon />
          <span className={styles.buttonText}>Account Settings</span>
        </div>
        <div className={styles.sideButton}>
          <ListIcon />
          <span className={styles.buttonText}>Manage Pastes</span>
        </div>
        <div className={styles.sideButton}>
          <FavoriteIcon />
          <span className={styles.buttonText}>Bookmarks</span>
        </div>
        <div className={styles.exitButton}>
          <ExitToAppIcon />
          <span className={styles.buttonText}>Return to site</span>
        </div>
      </div>

      <div className={styles.accountDetails}>
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
    </div>
  );
}
