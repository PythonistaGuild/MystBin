import React from "react";
import { Nav, Navbar } from "react-bootstrap";
import LoginIcon from "../icons/LoginIcon";
import LogoMain from "../public/LogoMain";
import styles from "../styles/Nav.module.css";
import OptsBar from "./OptsBar";

export default function NavBar() {
  return (
    <Navbar
      style={{
        backgroundColor: "#1B1B1B",
      }}
      variant={"dark"}
    >
      <Navbar.Brand href="#home" className={styles.logo}>
        <LogoMain />
      </Navbar.Brand>
      <Nav>
        <OptsBar />
      </Nav>
      <Nav className="ml-auto">
        <Nav.Link href="#deets">
          <LoginIcon />
        </Nav.Link>
      </Nav>
    </Navbar>
  );
}
