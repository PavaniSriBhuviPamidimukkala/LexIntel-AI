function Citation({data}) {

    return (

        <div>

            <hr />

            <p>
                📄 Source: {data.source}
            </p>

            <p>
                Page: {data.page}
            </p>

            <p>
                Section: {data.section}
            </p>

        </div>

    );
}


export default Citation;