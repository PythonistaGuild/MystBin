import {Nav, Navbar, OverlayTrigger, Popover} from "react-bootstrap";
import React from "react";
import EnhancedEncryptionIcon from '@material-ui/icons/EnhancedEncryption';
import HourglassFullIcon from '@material-ui/icons/HourglassFull';
import styles from "../styles/OptsBar.module.css"


export default function OptsBar() {
    const opts = [{title: "Create Password", content: "Create a password for this paste and all its files.", optional: true, icon: <EnhancedEncryptionIcon/>},
                  {title: "Create Expiry", content: "Create a expiry date for this paste and all its files.", optional: false, icon: <HourglassFullIcon />}]

    return (
        <Navbar className="justify-content-center">
            <Nav className={styles.optsNavContainer}>
                {opts.map((obj) => (
                    <OverlayTrigger
                        key={`opt-${obj.title}`}
                        placement={"bottom"}
                        overlay={
                            <Popover>
                                <Popover.Title
                                    className={styles.popoverHeader}
                                    as="h3">{obj.title}
                                </Popover.Title>
                                <Popover.Content>
                                    {obj.content}<strong> {obj.optional? "Optional": "Required"}</strong>
                                </Popover.Content>
                            </Popover>
                        }
                    >
                        {obj.icon}
                    </OverlayTrigger>
                    ))}
            </Nav>
        </Navbar>
    );
}